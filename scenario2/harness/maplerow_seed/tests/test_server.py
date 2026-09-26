import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request

import server


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ["ADMIN_PASSWORD"] = "test-password"
        os.environ["QUIET_LOG"] = "1"
        cls.httpd = server.make_server(0, os.path.join(cls.tmp.name, "test.db"))
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.opener = urllib.request.build_opener(_NoRedirect)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.tmp.cleanup()

    def post(self, fields):
        data = urllib.parse.urlencode(fields).encode()
        try:
            return self.opener.open(self.base + "/request", data=data)
        except urllib.error.HTTPError as err:
            return err

    def test_form_page_has_banner(self):
        with urllib.request.urlopen(self.base + "/") as resp:
            body = resp.read().decode()
            self.assertEqual(resp.status, 200)
        self.assertIn("PREVIEW", body)

    def test_valid_post_redirects(self):
        with self.post({"name": "Test Patient C", "phone": "519-555-0103", "consent": "yes"}) as resp:
            self.assertEqual(resp.status, 303)
            self.assertEqual(resp.headers["Location"], "/thanks")

    def test_post_without_consent_rejected(self):
        with self.post({"name": "Test Patient D", "phone": "519-555-0104"}) as resp:
            self.assertEqual(resp.status, 400)

    def test_admin_requires_auth(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(self.base + "/admin")
        ctx.exception.close()
        self.assertEqual(ctx.exception.code, 401)


if __name__ == "__main__":
    unittest.main()
