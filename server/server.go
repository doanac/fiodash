package server

import (
	"fmt"
	"net/http"
	"text/template"

	"github.com/foundriesio/fiodash/checks"
)

const indexTmpl string = `
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Fiodash</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.1/css/bulma.min.css">
  </head>
  <body>
  <section class="section">
    <div class="container">
      <h1 class="title">
        Checks Overview
      </h1>
      <p class="subtitle">
        High level view of device status.
	  </p>
	  <table class="table">
		<thead>
		  <tr><th>Check</th><th>Status</th><th>Details</th></tr>
		</thead>
		<tbody>
		{{range .Checks}}
			<tr>
			  <td><a href="/{{.Name}}">{{.Name}}</a></td>
			  <td {{.ValStyle}}>{{.Check.Status.Val}}</td>
			  <td>{{.Check.Status.Msg}}</td>
			</tr>
	    {{else}}
	    	<tr><td><strong>No Checks</strong></td></tr>
		{{end}}
		</tbody
	  </table>
	</div>
  </section>
  </body>
</html>
`

const detailsTmpl string = `
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Fiodash</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.1/css/bulma.min.css">
  </head>
  <body>
  <section class="section">
    <div class="container">
      <h1 class="title">
        Check for {{.Name}}
	  </h1>
	  <table class="table">
	  	<tr>
			<th>Status</th>
			<td><span {{.ValStyle}}>{{.Check.Status.Val}}</span></td>
		</tr>
		<tr>
			<th>Details</th>
			<td>{{.Check.Status.Msg}}</td>
		</tr>
	  </table>
	  <pre>{{.Log}}</pre>
	</div>
  </section>
  </body>
</html>
`

var index *template.Template
var details *template.Template

func indexHandler(w http.ResponseWriter, r *http.Request) {
	type row struct {
		Name     string
		Check    checks.Check
		ValStyle string
	}

	var rows []row
	e := checks.Iterate(func(name string, checkFunc checks.CheckFunc) error {
		check, err := checkFunc()
		if err != nil {
			check.Status.Msg = fmt.Sprintf("%s", err)
			check.Status.Val = checks.ERROR
		}
		valStyle := ""
		if check.Status.Val != checks.OK {
			valStyle = "class=\"is-danger\""
		}
		rows = append(rows, row{name, check, valStyle})
		return err
	})
	if e != nil {
		w.WriteHeader(http.StatusInternalServerError)
	}

	data := struct {
		Checks []row
	}{
		Checks: rows,
	}
	if e := index.Execute(w, data); e != nil {
		w.WriteHeader(http.StatusInternalServerError)
		fmt.Fprintf(w, "ERROR: %s", e)
	}
}

func checkDetails(name string, w http.ResponseWriter) {
	checkFunc, ok := checks.GetCheck(name)
	if ok {
		check, err := checkFunc()
		log := ""
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			check.Status.Msg = fmt.Sprintf("%s", err)
			check.Status.Val = checks.ERROR
		} else {
			log, err = check.GetLog()
			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				log = fmt.Sprintf("Unable to read logs: %s", err)
			}
		}
		valStyle := ""
		if check.Status.Val != checks.OK {
			valStyle = "class=\"is-danger\""
		}
		data := struct {
			Name     string
			Check    checks.Check
			Log      string
			ValStyle string
		}{
			Name:     name,
			Check:    check,
			Log:      log,
			ValStyle: valStyle,
		}
		if e := details.Execute(w, data); e != nil {
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "ERROR: %s", e)
		}
	} else {
		w.WriteHeader(http.StatusNotFound)
		fmt.Fprintf(w, "Check(%s) not found", name)
	}
}

func viewHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path == "/" {
		indexHandler(w, r)
		return
	}
	name := r.URL.Path[1:]
	checkDetails(name, w)
}

func Serve(port int) error {
	http.HandleFunc("/", viewHandler)
	return http.ListenAndServe(fmt.Sprintf(":%d", port), nil)
}

func init() {
	var err error
	index, err = template.New("index").Parse(indexTmpl)
	if err != nil {
		panic(err)
	}
	details, err = template.New("details").Parse(detailsTmpl)
	if err != nil {
		panic(err)
	}
}
