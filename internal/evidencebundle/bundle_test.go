package evidencebundle

import (
	"bytes"
	"strings"
	"testing"
)

func sample() Bundle {
	return Bundle{Format: Format, Version: Version, Title: "Evidence — örnek 🧭", Sources: []Source{{Alias: "s1", Kind: "filesystem", DisplayName: "Notes"}}, Entries: []Entry{
		{SourceAlias: "s1", RelativePath: "folder/quote.md", MediaType: "text/markdown", ContentHash: strings.Repeat("a", 64), StartChar: 17, Text: "повтор 🧪\nİstanbul", Note: "заметка\nsecond"},
		{SourceAlias: "s1", RelativePath: "file.pdf", MediaType: "application/pdf", ContentHash: strings.Repeat("0", 64), Page: 2, StartChar: 9, Text: "повтор 🧪", Note: "different note"},
	}}
}
func TestRoundTripCanonicalAndDigest(t *testing.T) {
	b := sample()
	encoded, err := Encode(b)
	if err != nil {
		t.Fatal(err)
	}
	decoded, err := Decode(bytes.NewReader(encoded))
	if err != nil {
		t.Fatal(err)
	}
	if len(decoded.Entries) != 2 || decoded.Entries[0].Text != "повтор 🧪\nİstanbul" || decoded.Entries[1].Page != 2 || decoded.Entries[1].Note != "different note" {
		t.Fatalf("round trip lost data: %#v", decoded)
	}
	again, err := Encode(decoded)
	if err != nil || !bytes.Equal(encoded, again) {
		t.Fatalf("not canonical: %v", err)
	}
	d1, err := Digest(b)
	if err != nil {
		t.Fatal(err)
	}
	d2, err := Digest(decoded)
	if err != nil || d1 != d2 {
		t.Fatal("digest mismatch")
	}
}
func TestStrictRejections(t *testing.T) {
	base := `{"format":"findrail-evidence-bundle","version":1,"title":"x","sources":[{"alias":"s1","kind":"filesystem","display_name":"x"}],"entries":[{"source_alias":"s1","relative_path":"a","media_type":"text/plain","content_hash":"` + strings.Repeat("a", 64) + `","page":0,"start_char":0,"text":"x","note":""}]}`
	cases := []string{
		strings.Replace(base, `"title":"x"`, `"title":"x","title":"y"`, 1),
		strings.Replace(base, `"display_name":"x"`, `"display_name":"x","display_name":"y"`, 1),
		strings.Replace(base, `"note":""`, `"note":"","note":"y"`, 1),
		strings.Replace(base, `"text":"x"`, `"text":"x","extra":true`, 1),
		strings.Replace(base, `"version":1`, `"version":1.0`, 1),
		strings.Replace(base, `"version":1`, `"version":999999999999999999999`, 1),
		strings.Replace(base, `"relative_path":"a"`, `"relative_path":"../a"`, 1),
		strings.Replace(base, `"relative_path":"a"`, `"relative_path":"https://example.test/a"`, 1),
		base + ` {}`, strings.Replace(base, `"source_alias":"s1"`, `"source_alias":"s2"`, 1),
	}
	for i, s := range cases {
		if _, err := Decode(strings.NewReader(s)); err == nil {
			t.Errorf("case %d accepted", i)
		}
	}
	if _, err := Decode(bytes.NewReader([]byte{0xff})); err == nil {
		t.Fatal("invalid UTF-8 accepted")
	}
}
func TestLimitsAndEmptyBundle(t *testing.T) {
	b := Bundle{Title: "empty", Sources: []Source{}, Entries: []Entry{}}
	raw, err := Encode(b)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = Decode(bytes.NewReader(raw)); err != nil {
		t.Fatal(err)
	}
	b = sample()
	b.Entries[0].StartChar = 2147483648
	if _, err = Encode(b); err == nil {
		t.Fatal("overflow start accepted")
	}
	b = sample()
	b.Entries[0].RelativePath = strings.Repeat("a", 2049)
	if _, err = Encode(b); err == nil {
		t.Fatal("oversize path accepted")
	}
	b = sample()
	b.Entries[0].Text = strings.Repeat("x", 256<<10+1)
	if _, err = Encode(b); err == nil {
		t.Fatal("oversize excerpt accepted")
	}
	if _, err := Decode(strings.NewReader(strings.Repeat(" ", MaxRaw+1))); err == nil {
		t.Fatal("oversize input accepted")
	}
}
