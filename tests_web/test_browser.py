"""Browser regression tests. Provider requests are mocked; no real keys needed."""
import functools
import json
import os
from pathlib import Path
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright, expect


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        web = Path(__file__).resolve().parents[1] / "web"
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(web)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            executable_path=os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE") or None,
            headless=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.requests = []

        def respond(route):
            self.requests.append(route.request.post_data_json)
            route.fulfill(json={"choices": [{"message": {"content": "A real test reply. <img src=x onerror=alert(1)>"}}]})

        self.page.route("https://openrouter.ai/api/v1/chat/completions", respond)
        self.page.goto(self.url)

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def connect(self):
        self.page.locator("#connection-status").click()
        self.page.locator("#api-key").fill("test-key-not-a-real-secret")
        self.page.get_by_role("button", name="Connect JARVIS").click()

    def send(self, text="Hello JARVIS"):
        self.page.locator("#prompt").fill(text)
        self.page.get_by_role("button", name="Send message", exact=True).click()

    def test_first_run_and_session_key(self):
        self.send()
        expect(self.page.locator("#settings-dialog")).to_be_visible()
        self.page.locator("#api-key").fill("test-key")
        self.page.get_by_role("button", name="Connect JARVIS").click()
        self.assertEqual(self.page.locator("#api-key").input_value(), "")
        self.assertEqual(self.page.evaluate("[localStorage.length, sessionStorage.length]"), [0, 0])
        self.page.reload()
        expect(self.page.locator("#status-label")).to_have_text("Add API key")

    def test_chat_context_safe_rendering_and_reset(self):
        self.connect()
        self.send()
        expect(self.page.locator(".assistant .message-content")).to_contain_text("A real test reply.")
        self.assertEqual(self.page.locator("#messages img").count(), 0)
        self.send("And then?")
        expect(self.page.locator(".assistant")).to_have_count(2)
        expect(self.page.locator("#stop-button")).to_be_hidden()
        roles = [m["role"] for m in self.requests[1]["messages"]]
        self.assertEqual(roles, ["system", "user", "assistant", "user"])
        self.page.locator("#new-chat").click()
        expect(self.page.locator("#welcome")).to_be_visible()
        expect(self.page.locator(".message")).to_have_count(0)

    def test_rate_limit_preserves_retry_and_excludes_failed_context(self):
        self.connect()
        self.page.route("https://openrouter.ai/api/v1/chat/completions", lambda route: route.fulfill(status=429, json={"error": {"message": "limited"}}), times=1)
        self.send("Retry me")
        expect(self.page.locator(".assistant .message-content")).to_contain_text("rate-limited")
        expect(self.page.locator("#prompt")).to_have_value("Retry me")
        self.page.locator("#send-button").click()
        expect(self.page.locator(".assistant").last).to_contain_text("A real test reply")
        self.assertEqual([m["role"] for m in self.requests[0]["messages"]], ["system", "user"])

    def test_empty_response_and_auth_error(self):
        self.connect()
        self.page.route("https://openrouter.ai/api/v1/chat/completions", lambda route: route.fulfill(json={"choices": [{"message": {"content": None}}]}), times=1)
        self.send()
        expect(self.page.locator(".assistant")).to_contain_text("no answer")
        self.page.route("https://openrouter.ai/api/v1/chat/completions", lambda route: route.fulfill(status=401, json={"error": {}}), times=1)
        self.send()
        expect(self.page.locator(".assistant").last).to_contain_text("key was rejected")

    def test_cancel(self):
        self.connect()
        self.page.evaluate("""() => {
          window.fetch = (_url, options) => new Promise((_resolve, reject) => {
            options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
          });
        }""")
        self.send()
        self.page.locator("#stop-button").click()
        expect(self.page.locator(".assistant")).to_contain_text("Response stopped")
        expect(self.page.locator("#send-button")).to_be_visible()

    def test_disconnect(self):
        self.connect()
        self.page.locator("#settings-button").click()
        self.page.locator("#disconnect").click()
        expect(self.page.locator("#status-label")).to_have_text("Add API key")
        self.send()
        expect(self.page.locator("#settings-dialog")).to_be_visible()
        self.assertEqual(self.requests, [])

    def test_mobile_layout_and_prompt_shortcut(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
        self.page.get_by_role("button", name="Make a plan").click()
        self.assertIn("practical plan", self.page.locator("#prompt").input_value())
        self.assertTrue(self.page.locator("#send-button").is_visible())

    def test_dictation_and_read_aloud_controls(self):
        self.page.add_init_script("""
          window.SpeechRecognition = class {
            start() { this.onstart(); this.onresult({results:[[{transcript:'Dictated message'}]]}); this.onend(); }
            stop() {} abort() {}
          };
        """)
        self.page.reload()
        self.page.locator("#mic-button").click()
        expect(self.page.locator("#prompt")).to_have_value("Dictated message")
        self.assertEqual(self.requests, [])
        self.page.locator("#speak-toggle").click()
        expect(self.page.locator("#speak-toggle")).to_have_attribute("aria-pressed", "true")


if __name__ == "__main__":
    unittest.main()
