#!/usr/bin/env python3
"""Compiled Findrail + real Chromium collection journey (synthetic fixture only)."""
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    binary = pathlib.Path(sys.argv[1]).resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="findrail-evidence-") as tmp:
        base = pathlib.Path(tmp)
        notes, index = base / "notes", base / "index"
        notes.mkdir()
        (notes / "synthetic.md").write_text("Synthetic evidence alpha passage. Another sentence.", encoding="utf-8")
        subprocess.run([str(binary), "index", "--data-dir", str(index), str(notes)], check=True,
                       timeout=30, capture_output=True, text=True)
        http_port = port()
        server = subprocess.Popen([str(binary), "serve", "--data-dir", str(index), "--no-sync",
                                   "--addr", f"127.0.0.1:{http_port}"], stdout=subprocess.DEVNULL,
                                  stderr=subprocess.PIPE, text=True)
        options = webdriver.ChromeOptions()
        options.binary_location = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome") or ""
        if not options.binary_location:
            raise RuntimeError("Chromium/Chrome binary not found in PATH")
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("prefs", {"download.default_directory": str(base),
                                                    "download.prompt_for_download": False})
        browser = None
        denied_fallback = None
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    raise RuntimeError("compiled Findrail exited: " + server.stderr.read())
                try:
                    import urllib.request
                    urllib.request.urlopen(f"http://127.0.0.1:{http_port}/healthz", timeout=1).read()
                    break
                except Exception:
                    time.sleep(.1)
            browser = webdriver.Chrome(options=options)
            browser.set_page_load_timeout(15)
            browser.get(f"http://127.0.0.1:{http_port}/")
            wait = WebDriverWait(browser, 10)
            query = wait.until(lambda d: d.find_element(By.ID, "query"))
            query.send_keys("alpha")
            browser.find_element(By.ID, "search-form").submit()
            preview_button = wait.until(lambda d: next((b for b in d.find_elements(By.TAG_NAME, "button")
                                                        if b.text == "Preview"), False))
            preview_button.click()
            wait.until(lambda d: d.find_element(By.ID, "preview-body").text.startswith("Synthetic"))
            browser.execute_script("""const b=document.getElementById('preview-body'),t=b.firstChild;
                const r=document.createRange();r.setStart(t,0);r.setEnd(t,Math.min(10,t.length));
                const s=getSelection();s.removeAllRanges();s.addRange(r);""")
            browser.find_element(By.ID, "add-evidence").click()
            pin_status=browser.execute_script("return document.getElementById('collection-status').textContent"); assert "added" in pin_status, pin_status
            browser.find_element(By.ID, "close-preview").click()
            browser.find_element(By.ID, "collection-open").click()
            wait.until(lambda d: len(d.find_elements(By.CLASS_NAME, "collection-row")) == 1)
            assert "Synthetic" in browser.execute_script("return document.getElementById('collection-list').textContent")
            clipboard_result = "unavailable"
            try:
                browser.execute_cdp_cmd("Browser.grantPermissions", {
                    "origin": f"http://127.0.0.1:{http_port}",
                    "permissions": ["clipboardReadWrite", "clipboardSanitizedWrite"],
                })
                browser.find_element(By.ID, "collection-copy").click()
                wait.until(lambda d: "copied" in d.execute_script(
                    "return document.getElementById('collection-status').textContent"))
                clipboard_text = browser.execute_async_script(
                    "const done=arguments[arguments.length-1];navigator.clipboard.readText().then(done).catch(e=>done('ERROR:'+e.name))")
                clipboard_result = "actual clipboard read/write" if clipboard_text.startswith("# Findrail") else "write supported; read restricted"
                for permission in ("clipboard-read", "clipboard-write"):
                    browser.execute_cdp_cmd("Browser.setPermission", {
                        "origin": f"http://127.0.0.1:{http_port}",
                        "permission": {"name": permission}, "setting": "denied",
                    })
                browser.find_element(By.ID, "collection-copy").click()
                wait.until(lambda d: not d.find_element(By.ID, "collection-fallback").get_attribute("hidden"))
                fallback = browser.execute_script("return document.getElementById('collection-output').value")
                denied_fallback = fallback
                clipboard_result += "; denied permission fallback matched"
            except Exception:
                clipboard_result = "browser denied/unavailable; accessible fallback available"
                fallback = browser.execute_script("return document.getElementById('collection-output').value")
                assert fallback.startswith("# Findrail"), fallback[:120]
            browser.find_element(By.ID, "collection-download").click()
            wait.until(lambda _: (base / "findrail-evidence.md").exists())
            exported = (base / "findrail-evidence.md").read_text(encoding="utf-8")
            assert "Synthetic" in exported and "file://" in exported
            if denied_fallback is not None:
                stable = lambda value: "\n".join(line for line in value.splitlines() if not line.startswith("Exported "))
                assert stable(denied_fallback) == stable(exported), "denied clipboard fallback differs from downloaded Markdown"
            browser.find_element(By.ID, "collection-clear").click()
            assert browser.find_element(By.ID, "collection-count").text == "0"
            browser.refresh()
            assert browser.find_element(By.ID, "collection-count").text == "0"
            caps = browser.capabilities
            print(f"Chromium {caps.get('browserVersion')} on {sys.platform}; compiled-server journey: search, preview, exact selected pin, inspect, clipboard ({clipboard_result}), downloaded Markdown bytes, clear, reload.")
        finally:
            if browser:
                browser.quit()
            server.terminate()
            try:
                server.wait(timeout=7)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)


if __name__ == "__main__":
    main()
