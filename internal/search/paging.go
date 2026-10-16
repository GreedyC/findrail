package search

// PageWindowLimit bounds the private position space available to a paged query.
const PageWindowLimit = 1000

// PageRequest carries a normal search request. Cursor is reserved for the
// consistency coordinator; this query component never interprets it.
type PageRequest struct {
	Request Request
	Cursor  string
}

// PageResult is a paged search result. The regular Result remains unchanged.
type PageResult struct {
	Result
	SnippetTruncated bool `json:"snippet_truncated"`
}

// PageResponse describes one bounded page; cursor fields are null until the
// consistency coordinator supplies continuation state.
type PageResponse struct {
	Results     []PageResult `json:"results"`
	Total       int          `json:"total"`
	Offset      int          `json:"offset"`
	Returned    int          `json:"returned"`
	Limit       int          `json:"limit"`
	WindowLimit int          `json:"window_limit"`
	NextCursor  *string      `json:"next_cursor"`
	EndReason   *string      `json:"end_reason"`
}
