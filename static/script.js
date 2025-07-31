async function saveNote() {
  const text = document.getElementById("note").value;
  const response = await fetch("/save", {
    method: "POST",
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ text })
  });
  const result = await response.json();
  alert("Note saved!");
  location.reload();
}

async function analyzeNote() {
  const text = document.getElementById("note").value;
  const response = await fetch("/analyze", {
    method: "POST",
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ text })
  });
  const result = await response.json();
  document.getElementById("result").innerText = result.result || result.error;
}

function logout() {
  window.location.href = "/logout";
}
