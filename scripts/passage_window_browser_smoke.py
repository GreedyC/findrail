#!/usr/bin/env python3
"""Real late text/DOCX citation, process restart, export and freshness journey."""
import json
import os
import pathlib
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import urllib.request

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

from smoke import docx_fixture


def main():
    binary = pathlib.Path(sys.argv[1]).resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="Findrail late passages – ") as temporary:
        root = pathlib.Path(temporary)
        notes, data = root / "fictional notes", root / "private index"
        notes.mkdir()
        text_quote, word_quote = "needletextlate exact text quote", "needledocxlate exact Word quote"
        (notes / "late.md").write_text("padding " * 10000 + text_quote + " 😀e\u0301\n", encoding="utf-8")
        (notes / "late.docx").write_bytes(docx_fixture("padding " * 10000 + word_quote + " 😀e\u0301"))
        subprocess.run([str(binary), "index", "--data-dir", str(data), str(notes)], check=True, capture_output=True, timeout=30)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        options = webdriver.ChromeOptions()
        options.binary_location = os.environ.get("FINDRAIL_CHROME") or shutil.which("chromium") or shutil.which("google-chrome") or ""
        for flag in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage"):
            options.add_argument(flag)
        driver = os.environ.get("FINDRAIL_CHROMEDRIVER") or shutil.which("chromedriver")
        browser = server = None

        def stop():
            nonlocal browser, server
            if browser:
                browser.quit()
                browser = None
            if server and server.poll() is None:
                server.terminate()
                try:
                    server.communicate(timeout=8)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.communicate(timeout=3)

        def launch():
            nonlocal browser, server
            server = subprocess.Popen([str(binary), "start", "--data-dir", str(data), "--no-open", "--sync-interval", "1s", "--addr", f"127.0.0.1:{port}"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            def ready(_):
                if server.poll() is not None:
                    raise AssertionError("passage server exited: " + server.stderr.read())
                try:
                    with urllib.request.urlopen(url + "/api/v1/capabilities", timeout=1) as response:
                        return json.load(response).get("passage_preview") is True
                except OSError:
                    return False
            WebDriverWait(None, 20).until(ready)
            browser = webdriver.Chrome(service=Service(executable_path=driver) if driver else Service(), options=options)
            browser.get(url + "/")
            WebDriverWait(browser, 20).until(lambda d: not d.find_element(By.ID, "collection-save").get_attribute("hidden"))

        def wait_for_quote(quote):
            WebDriverWait(browser, 20).until(lambda d: quote in d.find_element(By.ID, "preview-body").text)

        def open_result(query):
            field = browser.find_element(By.ID, "query")
            field.clear()
            field.send_keys(query)
            browser.find_element(By.ID, "submit").click()
            def click_matching(d):
                try:
                    for row in d.find_elements(By.CSS_SELECTOR, ".result"):
                        if query in row.text:
                            row.find_element(By.CSS_SELECTOR, ".location button").click()
                            return True
                except StaleElementReferenceException:
                    return False
                return False
            WebDriverWait(browser, 20).until(click_matching)

        def select_quote(quote):
            browser.execute_script("""
                const body=document.getElementById('preview-body'),quote=arguments[0];
                const at=body.textContent.indexOf(quote);if(at<0)throw Error('quote absent');
                const walker=document.createTreeWalker(body,NodeFilter.SHOW_TEXT);
                let n,position=0,start=null,end=null;
                while(n=walker.nextNode()){
                  if(!start&&at>=position&&at<position+n.length)start=[n,at-position];
                  if(at+quote.length>position&&at+quote.length<=position+n.length){end=[n,at+quote.length-position];break}
                  position+=n.length;
                }
                const range=document.createRange();range.setStart(...start);range.setEnd(...end);
                const selection=getSelection();selection.removeAllRanges();selection.addRange(range);
                document.dispatchEvent(new Event('selectionchange'));
            """, quote)

        try:
            launch()
            browser.find_element(By.ID, "collection-open").click()
            browser.find_element(By.ID, "collection-new").click()
            title = browser.find_element(By.ID, "collection-title")
            title.clear()
            title.send_keys("Late windows")
            browser.find_element(By.ID, "collection-close").click()
            for count, (query, quote) in enumerate((("needletextlate", text_quote), ("needledocxlate", word_quote)), 1):
                open_result(query)
                wait_for_quote(quote)
                notice = browser.find_element(By.ID, "preview-notice").text
                assert "indexed characters 80000" in notice, notice
                assert browser.find_element(By.ID, "next-text").get_attribute("disabled"), "a tail must not offer an empty next window"
                if count == 1:
                    browser.find_element(By.ID, "previous-text").click()
                    WebDriverWait(browser, 20).until(lambda d: d.find_element(By.ID, "text-range").text.startswith("14464–80000"))
                    browser.find_element(By.ID, "next-text").click()
                    wait_for_quote(quote)
                else:
                    assert "page numbers are unavailable" in notice
                select_quote(quote)
                browser.find_element(By.ID, "add-evidence").click()
                WebDriverWait(browser, 20).until(lambda d: d.find_element(By.ID, "collection-count").text == str(count))
                browser.find_element(By.ID, "close-preview").click()
            browser.find_element(By.ID, "collection-open").click()
            rows = browser.find_elements(By.CSS_SELECTOR, ".collection-row")
            rows[0].find_element(By.TAG_NAME, "textarea").send_keys("Late text note")
            rows[1].find_element(By.TAG_NAME, "textarea").send_keys("Late Word note")
            rows[0].find_element(By.XPATH, ".//button[.='Move down']").click()
            browser.find_element(By.ID, "collection-save").click()
            WebDriverWait(browser, 20).until(lambda d: "saved" in d.find_element(By.ID, "collection-status").text.lower() and not d.find_element(By.ID, "collection-save").get_attribute("disabled"))
            collection_id = browser.find_element(By.ID, "collection-picker").get_attribute("value")
            assert collection_id, "the named collection was not persisted"
            stop()
            with sqlite3.connect((data / "findrail.db").as_uri() + "?mode=ro", uri=True) as db:
                assert db.execute("PRAGMA user_version").fetchone()[0] == 8
                saved = [(start, json.loads(raw)) for start, raw in db.execute("SELECT preview_start_char,snapshot_json FROM evidence_collection_entries WHERE collection_id=? ORDER BY ordinal", (collection_id,))]
            assert [entry["excerpt"] for _, entry in saved] == [word_quote, text_quote]
            assert [entry["note"] for _, entry in saved] == ["Late Word note", "Late text note"]
            for start, entry in saved:
                assert start == entry["evidence"]["text_start_char"] == 80000
                assert entry["evidence"]["truncated"] is True
                assert entry["evidence"].get("page", 0) == 0
            launch()
            browser.find_element(By.ID, "collection-open").click()
            Select(browser.find_element(By.ID, "collection-picker")).select_by_value(collection_id)
            WebDriverWait(browser, 20).until(lambda d: d.find_element(By.ID, "collection-count").text == "2")
            restored = browser.find_elements(By.CSS_SELECTOR, ".collection-row")
            assert [row.find_element(By.TAG_NAME, "pre").text for row in restored] == [word_quote, text_quote]
            browser.find_element(By.ID, "collection-check").click()
            WebDriverWait(browser, 20).until(lambda d: d.find_element(By.ID, "collection-list").text.count("unchanged at last check") == 2)
            browser.execute_script("const original=URL.createObjectURL;URL.createObjectURL=function(blob){window.__passageDownload=blob.text();return original.call(this,blob)}")
            browser.find_element(By.ID, "collection-download").click()
            markdown = browser.execute_async_script("const done=arguments[0];window.__passageDownload.then(done)")
            assert all(value in markdown for value in (text_quote, word_quote, "Late text note", "Late Word note", (notes / "late.md").as_uri(), (notes / "late.docx").as_uri()))
            (notes / "late.md").write_text("Replacement short text with a different snapshot.", encoding="utf-8")
            old = saved[1][1]["evidence"]
            def changed(_):
                with urllib.request.urlopen(url + "/api/v1/documents/" + old["id"], timeout=2) as response:
                    return json.load(response)["content_hash"] != old["content_hash"]
            WebDriverWait(browser, 20).until(changed)
            browser.find_element(By.ID, "collection-check").click()
            WebDriverWait(browser, 20).until(lambda d: "changed/current version differs" in d.find_element(By.ID, "collection-list").text)
            assert text_quote in browser.find_element(By.ID, "collection-list").text
            print("Passage browser journey passed: late text/DOCX, manual windows, exact selection, note/order, process restart, Markdown and changed short document.")
        finally:
            stop()


if __name__ == "__main__":
    main()
