package checks

type StatusVal string

const (
	OK      StatusVal = "OK"
	ERROR   StatusVal = "ERROR"
	UNKNOWN StatusVal = "UNKNOWN"
)

type Status struct {
	Msg string
	Val StatusVal
}

type Link struct {
	Label string
	Url   string
}
type Check struct {
	Status Status
	Link   []Link
	GetLog func() (string, error)
}

var Checks = map[string]func() (Check, error){
	"aktualizr-lite": AkliteCheck,
	"docker":         func() (Check, error) { return DoSystemDCheck("docker") },
}
