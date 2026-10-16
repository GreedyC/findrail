package http

import (
	"strings"
	"testing"
	"time"

	"github.com/Lephiziel/findrail/internal/evidencebundle"
)

func TestEvidenceBundleClaimBindsDigestAndExpires(t *testing.T) {
	b := evidencebundle.Bundle{Title: "synthetic claim", Sources: []evidencebundle.Source{}, Entries: []evidencebundle.Entry{}}
	now := time.Date(2026, 10, 16, 12, 0, 0, 0, time.UTC)
	secret := []byte(strings.Repeat("k", 32))
	mappings := map[string]string{}
	token, err := signEvidenceBundleClaim(secret, b, mappings, "registration-binding", now.Add(5*time.Minute))
	if err != nil {
		t.Fatal(err)
	}
	claim, err := verifyEvidenceBundleClaim(secret, token, b, now)
	if err != nil || claim.Binding != "registration-binding" {
		t.Fatalf("valid claim=%+v err=%v", claim, err)
	}
	if _, err = verifyEvidenceBundleClaim(secret, token, b, now.Add(5*time.Minute+time.Second)); err == nil {
		t.Fatal("expired claim accepted")
	}
	tampered := "A" + token[1:]
	if token[0] == 'A' {
		tampered = "B" + token[1:]
	}
	if _, err = verifyEvidenceBundleClaim(secret, tampered, b, now); err == nil {
		t.Fatal("tampered claim accepted")
	}
	other := b
	other.Title = "another bundle"
	if _, err = verifyEvidenceBundleClaim(secret, token, other, now); err == nil {
		t.Fatal("cross-bundle claim accepted")
	}
}
