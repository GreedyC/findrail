#!/usr/bin/env python3
"""Fresh-index, UI-added-folder, restart browser journey on an extracted binary."""
import json
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

sys.dont_write_bytecode = True
from smoke import docx_fixture, pdf_fixture


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    binary = pathlib.Path(sys.argv[1]).resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="Findrail packaged journey – ") as temporary:
        base = pathlib.Path(temporary)
        root, data = base / "fixture notes – 雪", base / "new private index"
        root.mkdir()
        (root / "meeting notes.md").write_text(
            "idempotencymarker familiar synthetic note. <script>window.fixturePwned=true</script>", encoding="utf-8")
        (root / "runbook.pdf").write_bytes(pdf_fixture(["firstpage unique alpha", "secondpage page2journey unique beta"]))
        (root / "meeting.docx").write_bytes(docx_fixture("docxjourney unique word text"))
        port = free_port()
        address = f"127.0.0.1:{port}"
        url = f"http://{address}"
        browser = None

        def launch():
            return subprocess.Popen([str(binary), "start", "--data-dir", str(data), "--no-open", "--addr", address],
                                    cwd=base, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

        server = launch()

        def ready(proc):
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise AssertionError("candidate start exited: " + proc.stderr.read())
                try:
                    with urllib.request.urlopen(url + "/healthz", timeout=1) as response:
                        if response.status == 200:
                            return
                except (OSError, urllib.error.URLError):
                    time.sleep(.05)
            raise AssertionError("candidate loopback listener deadline expired")

        try:
            ready(server)
            options = webdriver.ChromeOptions()
            options.binary_location = os.environ.get("FINDRAIL_CHROME") or shutil.which("chromium") or shutil.which("google-chrome") or ""
            if not options.binary_location:
                raise RuntimeError("real Chromium/Chrome executable not found")
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_experimental_option("prefs", {"download.default_directory": str(base), "download.prompt_for_download": False})
            driver = os.environ.get("FINDRAIL_CHROMEDRIVER")
            browser = webdriver.Chrome(service=Service(executable_path=driver) if driver else Service(), options=options)
            browser.set_page_load_timeout(15)
            wait = WebDriverWait(browser, 20)
            browser.get(url + "/")
            wait.until(lambda d: not d.find_element(By.ID, "empty").get_attribute("hidden"))
            assert "empty" in browser.find_element(By.ID, "empty").text.lower()
            with urllib.request.urlopen(url + "/api/v1/sources", timeout=3) as response:
                assert json.load(response)["sources"] == [], "fresh start registered a source"
            browser.find_element(By.ID, "add-folder-open").click()
            browser.find_element(By.ID, "folder-path").send_keys(str(root.resolve()))
            browser.find_element(By.ID, "folder-form").submit()
            wait.until(lambda d: "succeeded" in d.find_element(By.ID, "management-status").text.lower())
            wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".source-card")) == 1)
            source_card = browser.find_element(By.CSS_SELECTOR, ".source-card")
            assert str(root.resolve()) in source_card.text and "DOCX enabled" in source_card.text, source_card.text

            def search(query, format_name="all"):
                browser.find_element(By.ID, "query").clear()
                browser.find_element(By.ID, "query").send_keys(query)
                Select(browser.find_element(By.ID, "format")).select_by_value(format_name)
                browser.find_element(By.ID, "search-form").submit()
                wait.until(lambda d: not d.find_element(By.ID, "submit").get_property("disabled")
                           and "matching documents" in d.find_element(By.ID, "status").text)
                assert "1 matching" in browser.find_element(By.ID, "status").text

            search("idempotencymarker")
            assert "1 matching" in browser.find_element(By.ID, "status").text
            browser.find_element(By.XPATH, "//button[.='Preview']").click()
            wait.until(lambda d: "idempotencymarker" in d.find_element(By.ID, "preview-body").text)
            assert browser.execute_script("return window.fixturePwned===true") is False
            selected = browser.execute_script("""
                const body=document.getElementById('preview-body');
                const walker=document.createTreeWalker(body,NodeFilter.SHOW_TEXT),nodes=[];
                let node; while(node=walker.nextNode()) if(node.length) nodes.push(node);
                const range=document.createRange(); range.setStart(nodes[0],0);
                let remaining=20;
                for(const text of nodes){
                    if(remaining<=text.length){range.setEnd(text,remaining);break}
                    remaining-=text.length;
                }
                const selection=getSelection();selection.removeAllRanges();selection.addRange(range);
                return selection.toString();
            """)
            assert selected == "idempotencymarker fa", selected
            browser.find_element(By.ID, "add-evidence").click()
            wait.until(lambda d: "added" in d.find_element(By.ID, "collection-status").get_property("textContent").lower())
            browser.find_element(By.ID, "add-evidence").click()
            assert "Duplicate" in browser.find_element(By.ID, "collection-status").get_property("textContent")
            browser.find_element(By.ID, "close-preview").click()
            search("page2journey", "pdf")
            browser.find_element(By.XPATH, "//button[.='Preview']").click()
            wait.until(lambda d: "Page 2 / 2" in d.find_element(By.ID, "page-label").text)
            assert "secondpage" in browser.find_element(By.ID, "preview-body").text
            browser.execute_script("document.getElementById('whole-preview').checked=true")
            browser.find_element(By.ID, "add-evidence").click()
            browser.find_element(By.ID, "close-preview").click()
            browser.find_element(By.ID, "collection-open").click()
            rows = browser.find_elements(By.CLASS_NAME, "collection-row")
            assert len(rows) == 2
            rows[0].find_element(By.TAG_NAME, "textarea").send_keys("note from packaged journey")
            browser.find_element(By.ID, "collection-download").click()
            deadline = time.monotonic() + 10
            exported = base / "findrail-evidence.md"
            while time.monotonic() < deadline and not exported.exists():
                time.sleep(.05)
            text = exported.read_text(encoding="utf-8")
            assert selected in text and "note from packaged journey" in text
            assert "runbook.pdf — page 2" in text and (root / "runbook.pdf").as_uri() + "#page=2" in text
            browser.find_element(By.ID, "collection-close").click()
            search("docxjourney", "docx")
            browser.find_element(By.XPATH, "//button[.='Preview']").click()
            wait.until(lambda d: "docxjourney" in d.find_element(By.ID, "preview-body").text)
            assert "page numbers are unavailable" in browser.find_element(By.ID, "preview-notice").text.lower()
            assert "page" not in browser.find_element(By.ID, "preview-meta").text.lower()
            browser.find_element(By.ID, "close-preview").click()
            browser.refresh()
            wait.until(lambda d: d.find_element(By.ID, "collection-count").text == "0")
            browser.quit(); browser = None
            server.terminate(); server.communicate(timeout=8)
            server = launch(); ready(server)
            browser = webdriver.Chrome(service=Service(executable_path=driver) if driver else Service(), options=options)
            browser.get(url + "/")
            wait = WebDriverWait(browser, 20)
            wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".source-card")) == 1)
            assert browser.find_element(By.ID, "collection-count").text == "0"
            search("idempotencymarker")
            assert "1 matching" in browser.find_element(By.ID, "status").text
            print("Packaged browser journey passed: empty start, UI Add folder, committed source/DOCX policy, search, preview, exact selected quote, duplicate, PDF page 2, Markdown bytes, reload and restart.")
        finally:
            if browser:
                browser.quit()
            if server.poll() is None:
                server.terminate()
                try:
                    server.communicate(timeout=8)
                except subprocess.TimeoutExpired:
                    server.kill(); server.communicate(timeout=3)


if __name__ == "__main__":
    main()
