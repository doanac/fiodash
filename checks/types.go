package checks

import (
	"io/ioutil"
)

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

type CheckFunc func() (Check, error)

type entry struct {
	Name string
	Func CheckFunc
}

var entries = []entry{}

func Iterate(cb func(name string, check CheckFunc) error) error {
	for _, entry := range entries {
		if e := cb(entry.Name, entry.Func); e != nil {
			return e
		}
	}
	return nil
}

func GetCheck(name string) (CheckFunc, bool) {
	for _, entry := range entries {
		if entry.Name == name {
			return entry.Func, true
		}
	}
	return nil, false
}

func init() {
	dockerFunc := func() (Check, error) { return DoSystemDCheck("docker") }
	entries = append(entries, entry{"aktualizr-lite", AkliteCheck})
	entries = append(entries, entry{"docker", dockerFunc})
	files, err := ioutil.ReadDir("/var/sota/compose")
	if err != nil {
		return
	}
	for _, f := range files {
		if f.IsDir() {
			check := func() (Check, error) { return ComposeCheck(f.Name()) }
			entries = append(entries, entry{f.Name(), check})
		}
	}
}
