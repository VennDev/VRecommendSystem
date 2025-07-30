package strings

import "time"

func DateTimeString() string {
	return time.Now().Format("2006-01-02")
}
