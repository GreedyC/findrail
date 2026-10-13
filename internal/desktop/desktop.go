// Package desktop contains process ownership primitives for the native launcher.
package desktop

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"
)

var ErrOwned = errors.New("a desktop instance already owns this data directory")

const recordName = ".desktop-instance.json"

type Record struct {
	Version int    `json:"version"`
	DataDir string `json:"data_dir"`
	URL     string `json:"url"`
	Nonce   string `json:"nonce"`
}

func NewRecord(dir, endpoint string) (Record, error) {
	var b [32]byte
	if _, err := rand.Read(b[:]); err != nil {
		return Record{}, err
	}
	return Record{Version: 1, DataDir: dir, URL: endpoint, Nonce: hex.EncodeToString(b[:])}, nil
}
func (l *Lock) Publish(r Record) error {
	if l == nil || r.DataDir != l.DataDir || !validEndpoint(r.URL) || len(r.Nonce) != 64 {
		return errors.New("invalid desktop instance record")
	}
	b, err := json.Marshal(r)
	if err != nil {
		return err
	}
	f, err := os.CreateTemp(l.DataDir, ".desktop-record-*")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	if err = f.Chmod(0600); err == nil {
		_, err = f.Write(b)
	}
	if err == nil {
		err = f.Sync()
	}
	if closeErr := f.Close(); err == nil {
		err = closeErr
	}
	if err != nil {
		return err
	}
	return os.Rename(name, filepath.Join(l.DataDir, recordName))
}
func (l *Lock) RemoveRecord() error {
	b, err := os.ReadFile(filepath.Join(l.DataDir, recordName))
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	var current Record
	if json.Unmarshal(b, &current) == nil && current.DataDir == l.DataDir {
		return os.Remove(filepath.Join(l.DataDir, recordName))
	}
	return nil
}
func ReadRecord(dir string) (Record, error) {
	abs, err := filepath.Abs(dir)
	if err != nil {
		return Record{}, err
	}
	abs, err = filepath.EvalSymlinks(abs)
	if err != nil {
		return Record{}, err
	}
	b, err := os.ReadFile(filepath.Join(abs, recordName))
	if err != nil {
		return Record{}, err
	}
	if len(b) > 4096 {
		return Record{}, errors.New("desktop instance record is oversized")
	}
	var r Record
	if err = json.Unmarshal(b, &r); err != nil {
		return Record{}, fmt.Errorf("invalid desktop instance record: %w", err)
	}
	if r.Version != 1 || r.DataDir != abs || !validEndpoint(r.URL) || len(r.Nonce) != 64 {
		return Record{}, errors.New("invalid desktop instance record")
	}
	return r, nil
}
func validEndpoint(raw string) bool {
	u, err := url.Parse(raw)
	if err != nil || u.Scheme != "http" || u.User != nil || u.Path != "" && u.Path != "/" || u.RawQuery != "" || u.Fragment != "" {
		return false
	}
	h, p, err := net.SplitHostPort(u.Host)
	if err != nil || p == "0" {
		return false
	}
	ip := net.ParseIP(strings.Trim(h, "[]"))
	return ip != nil && ip.IsLoopback()
}
func Verify(r Record) bool {
	client := http.Client{Timeout: 1500 * time.Millisecond, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	resp, err := client.Get(r.URL + "/api/v1/desktop/identity")
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return false
	}
	var got struct {
		Product string `json:"product"`
		DataDir string `json:"data_dir"`
		Nonce   string `json:"nonce"`
	}
	if json.NewDecoder(http.MaxBytesReader(nil, resp.Body, 1024)).Decode(&got) != nil {
		return false
	}
	return got.Product == "Findrail" && got.DataDir == r.DataDir && got.Nonce == r.Nonce
}
