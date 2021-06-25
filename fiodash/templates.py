INDEX_TPL = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FIO Dashboard</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.1/css/bulma.min.css">
    <script type="application/javascript">

function handleApps(errorPanel) {
  var form = document.getElementById("update-apps-form");
  var elements = form.elements;
  var button = document.getElementById("update-apps-btn");
  form.addEventListener("submit", event => {
    event.preventDefault()

    var apps = [];
    const formData = new FormData(form);
    button.textContent = "Enabling apps...";
    errorPanel.style.display = "none";
    console.log("Enabling apps");
    for (var pair of formData.entries()) {
      apps.push(pair[1]);
      console.log(" " + pair[1]);
    }

    // disable while we do this:
    for (var i = 0, len = elements.length; i < len; ++i) {
      elements[i].disabled = true;
    }

    fetch('/update-apps', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({"apps": apps}),
    })
    .then(response => {
      // renable:
      for (var i = 0, len = elements.length; i < len; ++i) {
        elements[i].disabled = false;
      }
      button.textContent = "Change apps";
      if (!response.ok) {
        throw response;
      }
    })
    .catch((error) => {
      console.error('Error:', error);
      try {
        error.text().then(body => {
          errorPanel.innerHTML = "Unable to change apps: " + body;
        });
      } catch (e) {
        errorPanel.innerHTML = "Unable to change apps: " + e;
      }
      errorPanel.style.display = "block";
    });
  })
}

function handleOta(errorPanel) {
  var form = document.getElementById("update-target-form");
  % if latest.name == current_target.name:
  form.style.display = "none";
  % end
  var elements = form.elements;
  var button = document.getElementById("update-target-btn");
  form.addEventListener("submit", event => {
    event.preventDefault()

    // disable while we do this:
    for (var i = 0, len = elements.length; i < len; ++i) {
      elements[i].disabled = true;
    }

    fetch('/update-target', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
    })
    .then(response => {
      // renable:
      for (var i = 0, len = elements.length; i < len; ++i) {
        elements[i].disabled = false;
      }
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      if (response.status == 202) {
        alert("REBOOTING DEVICE!!!!")
      } else {
        location.reload();
      }
    })
    .catch((error) => {
      console.error('Error:', error);
      errorPanel.innerHTML = "Unable to update: " + error;
      errorPanel.style.display = "block";
    });
  })
}

document.addEventListener("DOMContentLoaded", () => {
  var errorPanel = document.getElementById("error-panel");
  errorPanel.style.display = "none";
  handleApps(errorPanel);
  handleOta(errorPanel);
});
    </script>
  </head>
  <body>
  <section class="section">
    <div class="container">
      <h1 class="title">FIO Dashboard</h1>
      <p class="subtitle">
        Device Name: {{name}}<br/>
        Device UUID: {{uuid}}
      </p>
      <table class="table">
       <tbody>
         <tr>
           <th>Version</th>
           <td>
           {{current_target.version}}
           <form id="update-target-form"><button id="update-target-btn" class="button is-warning">Update to: {{latest.name}}</button></form>
           </td>
         </tr>
         <tr>
           <th>OSTree Hash</th>
           <td>{{current_target.sha256}}</td>
         </tr>
         <tr>
           <th>Apps</th>
           <td>
             <form id="update-apps-form">
             % for app in apps:
               <div>
               % if single_app:
                 <input type="radio" name="app" value="{{app['name']}}" {{"checked" if app['enabled'] else ""}}>
               % else:
                 <input type="checkbox" name="app" value="{{app['name']}}" {{"checked" if app['enabled'] else ""}}>
               % end
                 <label>{{app['name']}}</label>
               </div>
             % end
             <button id="update-apps-btn" type="submit">Change apps</button>
             </form>
             <div id="error-panel" class="notification is-danger">foo bar</div>
           </td>
        </tr>
       </tbody>
      </table>
    </div>
  </section>
  </body>
</html>
"""
