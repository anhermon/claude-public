// Form behaviour: inline validation messages, honeypot, POST JSON to data-endpoint, mailto fallback, clear states.
// <form class="form" data-endpoint="https://..." data-mailto="you@example.com" novalidate> ... </form>
// No endpoint yet? Leave data-endpoint empty: the form opens a pre-filled email instead (honest, works today).
(function () {
  "use strict";
  document.querySelectorAll("form.form").forEach(function (form) {
    var status = form.querySelector(".form-status"), btn = form.querySelector("button[type=submit]");
    function say(state, msg) { status.dataset.state = state; status.textContent = msg; }
    function check(el) {
      var err = document.getElementById(el.getAttribute("aria-describedby") || "") ;
      var bad = !el.checkValidity();
      el.setAttribute("aria-invalid", bad ? "true" : "false");
      if (err && err.classList.contains("f-err")) err.textContent = bad ? (el.dataset.msg || el.validationMessage) : "";
      return !bad;
    }
    form.querySelectorAll("input, textarea, select").forEach(function (el) {
      el.addEventListener("blur", function () { if (el.value || el.checked) check(el); });
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var fields = [].slice.call(form.elements).filter(function (el) { return el.name && !el.closest(".hp"); });
      var ok = fields.map(check).every(Boolean);
      if (!ok) { var first = form.querySelector("[aria-invalid=true]"); if (first) first.focus(); say("err", "Please fix the highlighted fields."); return; }
      var hp = form.querySelector(".hp input");
      if (hp && hp.value) { form.reset(); say("ok", "Thanks, received."); return; } // bot: pretend success, send nothing
      var data = {}; fields.forEach(function (el) { data[el.name] = el.type === "checkbox" ? el.checked : el.value.trim(); });
      var endpoint = form.dataset.endpoint, mailto = form.dataset.mailto;
      function viaMail() {
        if (!mailto) { say("err", "Couldn't send. Please try again later."); return; }
        var body = Object.keys(data).map(function (k) { return k + ": " + data[k]; }).join("\n");
        say("ok", "Your mail app is opening with the message filled in.");
        location.href = "mailto:" + mailto + "?subject=" + encodeURIComponent(form.dataset.subject || "Website enquiry") + "&body=" + encodeURIComponent(body);
      }
      if (!endpoint) return viaMail();
      btn.disabled = true; say("", "Sending…");
      var ctl = new AbortController(), timer = setTimeout(function () { ctl.abort(); }, 10000);
      fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data), signal: ctl.signal })
        .then(function (r) { clearTimeout(timer); btn.disabled = false;
          if (r.ok) { form.reset(); say("ok", form.dataset.okMsg || "Sent. You'll get a reply by email."); }
          else if (r.status === 422 || r.status === 429) r.json().then(function (d) { say("err", d.error || "Please check the form."); }, function () { say("err", "Please check the form."); });
          else viaMail(); })
        .catch(function () { clearTimeout(timer); btn.disabled = false; viaMail(); });
    });
  });
})();
