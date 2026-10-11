package ignorepolicy

import (
	"context"
	"strings"
	"testing"
)

func TestRules(t *testing.T) {
	p, err := Parse(context.Background(), []byte("*.log\n/notes/*\n!/notes/keep.md\nnotes/**/draft-?.md\n"))
	if err != nil {
		t.Fatal(err)
	}
	for _, tc := range []struct {
		path      string
		dir, want bool
	}{{"a/x.log", false, true}, {"x.log", false, true}, {"notes/keep.md", false, false}, {"notes/a/draft-1.md", false, true}, {"notes/draft-1.md", false, true}} {
		got := p.Decide(context.Background(), tc.path, tc.dir).Excluded
		if got != tc.want {
			t.Errorf("%s excluded=%v want %v", tc.path, got, tc.want)
		}
	}
}
func TestSyntaxAndBounds(t *testing.T) {
	for _, s := range []string{"a**b\n", "../x\n", "[a]\n", "C:/x\n"} {
		if _, err := Parse(context.Background(), []byte(s)); err == nil {
			t.Errorf("accepted %q", s)
		}
	}
	if ValidatePath("../secret") == nil {
		t.Fatal("traversal accepted")
	}
}
func TestBOMCommentEscapesAndUnicode(t *testing.T) {
	p, e := Parse(context.Background(), []byte("\xef\xbb\xbf# comment\r\n\\#literal\r\n?/é.txt\r\n"))
	if e != nil {
		t.Fatal(e)
	}
	if !p.Decide(context.Background(), "#literal", false).Excluded || !p.Decide(context.Background(), "x/é.txt", false).Excluded {
		t.Fatal("expected matching rules")
	}
}
func FuzzParseAndMatch(f *testing.F) {
	f.Add("*.log\n", "a.log")
	f.Add("/cache/**\n", "cache/a")
	f.Fuzz(func(t *testing.T, raw, path string) {
		if len(raw) > MaxInput || len(path) > MaxPathBytes {
			return
		}
		p, e := Parse(context.Background(), []byte(raw))
		if e == nil {
			_ = p.Decide(context.Background(), path, false)
		} else if len(e.Error()) > 128 {
			t.Fatal("unbounded error")
		}
	})
}

func BenchmarkNearLimitMatch(b *testing.B) {
	line := strings.Repeat("a*/", MaxPatternSegments-1) + "a*\n"
	raw := strings.Repeat(line, MaxRules)
	p, err := Parse(context.Background(), []byte(raw))
	if err != nil {
		b.Fatal(err)
	}
	path := strings.Repeat("abcdefghijklmno/", MaxPathSegments-1) + "abcdefghijklmno"
	b.SetBytes(int64(len(raw) + len(path)))
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = p.Decide(context.Background(), path, false)
	}
}
