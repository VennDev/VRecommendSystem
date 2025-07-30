package event

// Event types - exactly like your struct
const (
	VIEW = iota
	LIKE
	COMMENT
	SHARE
	BOOKMARK
	ADD_TO_CART
	ADD_TO_FAVORITES
	BUY
	CLICK
	REMOVE_FROM_CART
	REMOVE_FROM_FAVORITES
	SEARCH
	FILTER
	SORT
	SKIP
	HIDE
	DISLIKE
	RETURN
	DWELL_TIME
	SESSION_START
	SESSION_END
)

// Event names mapping
var EventNames = map[int]string{
	VIEW:                  "view",
	LIKE:                  "like",
	COMMENT:               "comment",
	SHARE:                 "share",
	BOOKMARK:              "bookmark",
	ADD_TO_CART:           "add_to_cart",
	ADD_TO_FAVORITES:      "add_to_favorites",
	BUY:                   "buy",
	CLICK:                 "click",
	REMOVE_FROM_CART:      "remove_from_cart",
	REMOVE_FROM_FAVORITES: "remove_from_favorites",
	SEARCH:                "search",
	FILTER:                "filter",
	SORT:                  "sort",
	SKIP:                  "skip",
	HIDE:                  "hide",
	DISLIKE:               "dislike",
	RETURN:                "return",
	DWELL_TIME:            "dwell_time",
	SESSION_START:         "session_start",
	SESSION_END:           "session_end",
}

// Event weights for recommendation scoring
var EventWeights = map[int]float64{
	VIEW:                  1.0,
	CLICK:                 1.5,
	LIKE:                  2.0,
	COMMENT:               3.0,
	SHARE:                 4.0,
	BOOKMARK:              3.5,
	ADD_TO_CART:           5.0,
	ADD_TO_FAVORITES:      4.0,
	BUY:                   10.0,
	SEARCH:                1.2,
	FILTER:                1.1,
	SORT:                  1.1,
	REMOVE_FROM_CART:      -2.0,
	REMOVE_FROM_FAVORITES: -1.5,
	SKIP:                  -0.5,
	HIDE:                  -1.0,
	DISLIKE:               -3.0,
	RETURN:                -5.0,
	DWELL_TIME:            2.0,
	SESSION_START:         0.1,
	SESSION_END:           0.1,
}
