(function () {
  var form = document.getElementById("request-form");
  if (!form) return;
  var error = document.getElementById("form-error");
  form.addEventListener("submit", function (event) {
    var missing = [];
    ["name", "phone"].forEach(function (id) {
      var field = document.getElementById(id);
      if (field && !field.value.trim()) missing.push(field.labels.length ? field.labels[0].textContent : id);
    });
    var consent = document.getElementById("consent");
    if (consent && !consent.checked) missing.push("Consent");
    if (missing.length) {
      event.preventDefault();
      error.textContent = "Please fill in: " + missing.join(", ");
      error.hidden = false;
    }
  });
})();
