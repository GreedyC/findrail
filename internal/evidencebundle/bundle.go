// Package evidencebundle encodes portable, selected evidence without provenance
// authority or any storage and filesystem dependencies.
package evidencebundle

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"regexp"
	"strings"
	"unicode/utf8"
)

const (
	Format     = "findrail-evidence-bundle"
	Version    = 1
	MaxRaw     = 4 << 20
	MaxEntries = 40
	MaxSources = 40
)

var ErrInvalid = errors.New("invalid evidence bundle")
var ErrLimit = errors.New("evidence bundle limit exceeded")

type Bundle struct {
	Format  string   `json:"format"`
	Version int      `json:"version"`
	Title   string   `json:"title"`
	Sources []Source `json:"sources"`
	Entries []Entry  `json:"entries"`
}
type Source struct {
	Alias       string `json:"alias"`
	Kind        string `json:"kind"`
	DisplayName string `json:"display_name"`
}
type Entry struct {
	SourceAlias  string `json:"source_alias"`
	RelativePath string `json:"relative_path"`
	MediaType    string `json:"media_type"`
	ContentHash  string `json:"content_hash"`
	Page         int    `json:"page"`
	StartChar    int    `json:"start_char"`
	Text         string `json:"text"`
	Note         string `json:"note"`
}

var hashPattern = regexp.MustCompile(`^[0-9a-f]{64}$`)
var aliasPattern = regexp.MustCompile(`^s([1-9]|[1-3][0-9]|40)$`)

// Decode reads at most MaxRaw+1 bytes, rejects non-UTF-8 and structurally
// ambiguous JSON, then returns a validated owned value.
func Decode(r io.Reader) (Bundle, error) {
	var zero Bundle
	b, err := io.ReadAll(io.LimitReader(r, MaxRaw+1))
	if err != nil {
		return zero, err
	}
	if len(b) > MaxRaw {
		return zero, ErrLimit
	}
	if !utf8.Valid(b) {
		return zero, ErrInvalid
	}
	if err := checkJSON(b); err != nil {
		return zero, err
	}
	var out Bundle
	d := json.NewDecoder(bytes.NewReader(b))
	d.DisallowUnknownFields()
	if err := d.Decode(&out); err != nil {
		return zero, ErrInvalid
	}
	if err := required(b, []string{"format", "version", "title", "sources", "entries"}); err != nil {
		return zero, err
	}
	if err := validate(out); err != nil {
		return zero, err
	}
	return out, nil
}

func Encode(b Bundle) ([]byte, error) {
	if err := validate(b); err != nil {
		return nil, err
	}
	b.Format, b.Version = Format, Version
	out, err := json.Marshal(b)
	if err != nil {
		return nil, ErrInvalid
	}
	if len(out) > MaxRaw {
		return nil, ErrLimit
	}
	return out, nil
}

// Digest is SHA-256 of Encode's canonical JSON bytes, not an authenticity proof.
func Digest(b Bundle) (string, error) {
	data, err := Encode(b)
	if err != nil {
		return "", err
	}
	h := sha256.Sum256(data)
	return hex.EncodeToString(h[:]), nil
}

func validate(b Bundle) error {
	if b.Format != "" && b.Format != Format || b.Version != 0 && b.Version != Version {
		return ErrInvalid
	}
	if strings.TrimSpace(b.Title) == "" || len(b.Title) > 256 || !utf8.ValidString(b.Title) || strings.IndexByte(b.Title, 0) >= 0 {
		return ErrInvalid
	}
	if len(b.Sources) > MaxSources || len(b.Entries) > MaxEntries {
		return ErrLimit
	}
	aliases := make(map[string]bool, len(b.Sources))
	for _, s := range b.Sources {
		if !aliasPattern.MatchString(s.Alias) || aliases[s.Alias] || len(s.DisplayName) > 512 || !utf8.ValidString(s.DisplayName) || strings.IndexByte(s.DisplayName, 0) >= 0 {
			return ErrInvalid
		}
		switch s.Kind {
		case "filesystem", "github", "archive":
		default:
			return ErrInvalid
		}
		aliases[s.Alias] = false
	}
	total := 0
	for _, e := range b.Entries {
		if _, ok := aliases[e.SourceAlias]; !ok {
			return ErrInvalid
		}
		aliases[e.SourceAlias] = true
		if !validPath(e.RelativePath) || len(e.RelativePath) > 2048 || utf8.RuneCountInString(e.RelativePath) > 512 || len(e.MediaType) > 255 || strings.TrimSpace(e.MediaType) == "" || !utf8.ValidString(e.MediaType) || strings.IndexByte(e.MediaType, 0) >= 0 || !hashPattern.MatchString(e.ContentHash) || e.StartChar < 0 || e.StartChar > 2147483647 {
			return ErrInvalid
		}
		if e.MediaType == "application/pdf" {
			if e.Page < 1 || e.Page > 100000 {
				return ErrInvalid
			}
		} else if e.Page != 0 {
			return ErrInvalid
		}
		meta, err := json.Marshal(struct {
			SourceAlias  string `json:"source_alias"`
			RelativePath string `json:"relative_path"`
			MediaType    string `json:"media_type"`
			ContentHash  string `json:"content_hash"`
			Page         int    `json:"page"`
			StartChar    int    `json:"start_char"`
		}{e.SourceAlias, e.RelativePath, e.MediaType, e.ContentHash, e.Page, e.StartChar})
		if err != nil || len(meta) > 16<<10 || len(e.Text) == 0 || len(e.Text) > 256<<10 || utf8.RuneCountInString(e.Text) > 65536 || len(e.Note) > 2048 || !utf8.ValidString(e.Text) || !utf8.ValidString(e.Note) || strings.IndexByte(e.Text, 0) >= 0 || strings.IndexByte(e.Note, 0) >= 0 {
			return ErrInvalid
		}
		total += len(e.Text)
		if total > 2<<20 {
			return ErrLimit
		}
	}
	for _, used := range aliases {
		if !used {
			return ErrInvalid
		}
	}
	return nil
}
func validPath(p string) bool {
	if p == "" || strings.HasPrefix(p, "/") || strings.ContainsAny(p, "\\\x00:") || strings.HasPrefix(p, "//") {
		return false
	}
	for _, part := range strings.Split(p, "/") {
		if part == "" || part == "." || part == ".." {
			return false
		}
	}
	return utf8.ValidString(p)
}

func checkJSON(data []byte) error {
	d := json.NewDecoder(bytes.NewReader(data))
	if err := walk(d, 0); err != nil {
		return err
	}
	if _, err := d.Token(); err != io.EOF {
		return ErrInvalid
	}
	return nil
}
func walk(d *json.Decoder, depth int) error {
	if depth > 16 {
		return ErrLimit
	}
	t, err := d.Token()
	if err != nil {
		return ErrInvalid
	}
	switch t {
	case json.Delim('{'):
		seen := map[string]bool{}
		for d.More() {
			k, e := d.Token()
			if e != nil {
				return ErrInvalid
			}
			key, ok := k.(string)
			if !ok || seen[key] {
				return ErrInvalid
			}
			seen[key] = true
			if e = walk(d, depth+1); e != nil {
				return e
			}
		}
		_, err = d.Token()
	case json.Delim('['):
		for d.More() {
			if err = walk(d, depth+1); err != nil {
				return err
			}
		}
		_, err = d.Token()
	}
	if err != nil {
		return ErrInvalid
	}
	return nil
}
func required(data []byte, names []string) error {
	var m map[string]json.RawMessage
	if json.Unmarshal(data, &m) != nil {
		return ErrInvalid
	}
	for _, n := range names {
		if _, ok := m[n]; !ok {
			return ErrInvalid
		}
	}
	var ss []json.RawMessage
	if json.Unmarshal(m["sources"], &ss) != nil {
		return ErrInvalid
	}
	for _, v := range ss {
		var x map[string]json.RawMessage
		if json.Unmarshal(v, &x) != nil {
			return ErrInvalid
		}
		for _, k := range []string{"alias", "kind", "display_name"} {
			if _, ok := x[k]; !ok {
				return ErrInvalid
			}
		}
	}
	var es []json.RawMessage
	if json.Unmarshal(m["entries"], &es) != nil {
		return ErrInvalid
	}
	for _, v := range es {
		var x map[string]json.RawMessage
		if json.Unmarshal(v, &x) != nil {
			return ErrInvalid
		}
		for _, k := range []string{"source_alias", "relative_path", "media_type", "content_hash", "page", "start_char", "text", "note"} {
			if _, ok := x[k]; !ok {
				return ErrInvalid
			}
		}
	}
	return nil
}
