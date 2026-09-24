// ----- Helper functions -----
const messageBox = document.getElementById("message");

function showMessage(text, type) {
  // type: "success" or "error"
  messageBox.textContent = text;
  messageBox.className = "message " + type;
  // Hide the message after a few seconds
  setTimeout(() => messageBox.classList.add("hidden"), 4000);
}

async function api(url, options = {}) {
  const res = await fetch(url, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || "Something went wrong");
  }
  return data;
}

// ----- Book list rendering -----
function renderBooks(books) {
  const list = document.getElementById("bookList");
  const listMessage = document.getElementById("listMessage");

  if (books.length === 0) {
    listMessage.textContent = "No books found.";
    list.innerHTML = "";
    return;
  }
  listMessage.textContent = books.length + " book(s) found.";

  list.innerHTML = books.map((book) => {
    const status = book.available
      ? '<span class="badge available">Available</span>'
      : '<span class="badge issued">Issued</span>';
    const issuedTo = book.issued_to_name
      ? '<span class="issued-to">' + book.issued_to_name + "</span>"
      : "-";
    let actions = "";
    if (book.available) {
      actions += '<button class="small success" onclick="issueBook(' +
        book.id + ')">Issue</button> ';
    } else {
      actions += '<button class="small secondary" onclick="returnBook(' +
        book.id + ')">Return</button> ';
    }
    actions += '<button class="small danger" onclick="deleteBook(' +
      book.id + ')">Delete</button>';

    return (
      "<tr>" +
      "<td>" + book.id + "</td>" +
      "<td>" + escapeHtml(book.title) + "</td>" +
      "<td>" + escapeHtml(book.author) + "</td>" +
      "<td>" + escapeHtml(book.isbn) + "</td>" +
      "<td>" + escapeHtml(book.category || "-") + "</td>" +
      "<td>" + status + "</td>" +
      "<td>" + issuedTo + "</td>" +
      "<td class=\"actions\">" + actions + "</td>" +
      "</tr>"
    );
  }).join("");
}

function escapeHtml(text) {
  // Prevent XSS when rendering unknown input
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

async function refreshBooks() {
  try {
    const data = await api("/api/books");
    renderBooks(data);
  } catch (err) {
    showMessage(err.message, "error");
  }
}

// ----- Members -----
function renderMembers(members) {
  const list = document.getElementById("memberList");
  const msg = document.getElementById("memberListMessage");

  if (members.length === 0) {
    msg.textContent = "No members yet.";
    list.innerHTML = "";
    return;
  }
  msg.textContent = members.length + " member(s).";

  list.innerHTML = members.map((m) => {
    return (
      "<tr>" +
      "<td>" + m.id + "</td>" +
      "<td>" + escapeHtml(m.name) + "</td>" +
      "<td>" + escapeHtml(m.email || "-") + "</td>" +
      '<td class="actions">' +
      '<button class="small danger" onclick="deleteMember(' + m.id + ')">Delete</button>' +
      "</td>" +
      "</tr>"
    );
  }).join("");
}

async function loadMembers() {
  try {
    const members = await api("/api/members");
    renderMembers(members);
  } catch (err) {
    showMessage(err.message, "error");
  }
}

async function deleteMember(memberId) {
  if (!confirm("Delete this member?")) return;
  try {
    const data = await api("/api/members/" + memberId, { method: "DELETE" });
    showMessage(data.message, "success");
    loadMembers();
  } catch (err) {
    showMessage(err.message, "error");
  }
}

// ----- Member autocomplete (type-ahead) -----
let selectedMemberId = null;
let memberResults = [];
let memberSearchTimer = null;

const memberInput = document.getElementById("memberSearch");
const suggestionsBox = document.getElementById("memberSuggestions");
const selectedBox = document.getElementById("selectedMember");
const selectedMemberLabel = document.getElementById("selectedMemberLabel");

function hideSuggestions() {
  suggestionsBox.classList.add("hidden");
}

function showSuggestions() {
  suggestionsBox.classList.remove("hidden");
}

function renderSuggestions(members) {
  memberResults = members;
  if (members.length === 0) {
    suggestionsBox.innerHTML = '<div class="suggestion none">No members found</div>';
    showSuggestions();
    return;
  }
  suggestionsBox.innerHTML = members.map((m) =>
    '<button type="button" class="suggestion" onclick="selectMember(' + m.id + ')">' +
    "<strong>" + escapeHtml(m.name) + "</strong>" +
    (m.email ? '<span class="suggestion-email">' + escapeHtml(m.email) + "</span>" : "") +
    "</button>"
  ).join("");
  showSuggestions();
}

async function searchMembers(q) {
  try {
    const members = await api("/api/members/search?q=" + encodeURIComponent(q));
    renderSuggestions(members);
  } catch (err) {
    hideSuggestions();
    showMessage(err.message, "error");
  }
}

function selectMember(id) {
  const member = memberResults.find((m) => m.id === id);
  if (!member) return;
  selectedMemberId = member.id;
  memberInput.value = member.name;
  selectedMemberLabel.textContent = "Selected member: " + member.name + " (ID " + member.id + ")";
  selectedBox.classList.remove("hidden");
  hideSuggestions();
}

function clearSelectedMember() {
  selectedMemberId = null;
  memberInput.value = "";
  memberResults = [];
  selectedBox.classList.add("hidden");
  hideSuggestions();
}

memberInput.addEventListener("input", () => {
  clearTimeout(memberSearchTimer);
  const q = memberInput.value.trim();
  selectedBox.classList.add("hidden");
  if (q.length < 2) {
    selectedMemberId = null;
    hideSuggestions();
    return;
  }
  selectedMemberId = null;
  memberSearchTimer = setTimeout(() => searchMembers(q), 250);
});

// Hide suggestions when clicking outside the search box
document.addEventListener("click", (e) => {
  if (!e.target.closest(".member-picker")) {
    hideSuggestions();
  }
});

document.getElementById("clearSelectedMember").addEventListener("click", clearSelectedMember);

// ----- RBU email suffix hint -----
const memberEmailInput = document.getElementById("memberEmail");
const emailDomainSuffix = document.getElementById("emailDomainSuffix");

function syncEmailSuffix() {
  emailDomainSuffix.style.display = memberEmailInput.value.includes("@") ? "none" : "";
}

memberEmailInput.addEventListener("input", syncEmailSuffix);

// ----- Event handlers -----
document.getElementById("addBookForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    title: document.getElementById("title").value,
    author: document.getElementById("author").value,
    isbn: document.getElementById("isbn").value,
    category: document.getElementById("category").value
  };
  try {
    await api("/api/books", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    showMessage("Book added successfully", "success");
    document.getElementById("addBookForm").reset();
    refreshBooks();
  } catch (err) {
    showMessage(err.message, "error");
  }
});

document.getElementById("addMemberForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    name: document.getElementById("memberName").value,
    email: document.getElementById("memberEmail").value
  };
  try {
    const member = await api("/api/members", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    showMessage("Member added successfully (ID " + member.id + ")", "success");
    document.getElementById("addMemberForm").reset();
    syncEmailSuffix();
    loadMembers();
  } catch (err) {
    showMessage(err.message, "error");
  }
});

document.getElementById("searchForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = document.getElementById("searchInput").value.trim();
  try {
    const data = await api("/api/books/search?q=" + encodeURIComponent(q));
    renderBooks(data);
  } catch (err) {
    showMessage(err.message, "error");
  }
});

document.getElementById("clearSearch").addEventListener("click", () => {
  document.getElementById("searchInput").value = "";
  refreshBooks();
});

async function issueBook(bookId) {
  if (!selectedMemberId) {
    showMessage("Please search and select a member first", "error");
    return;
  }
  try {
    const data = await api("/api/books/" + bookId + "/issue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ member_id: selectedMemberId })
    });
    showMessage(data.message, "success");
    refreshBooks();
  } catch (err) {
    showMessage(err.message, "error");
  }
}

async function returnBook(bookId) {
  try {
    const data = await api("/api/books/" + bookId + "/return", { method: "POST" });
    showMessage(data.message, "success");
    refreshBooks();
  } catch (err) {
    showMessage(err.message, "error");
  }
}

async function deleteBook(bookId) {
  if (!confirm("Delete this book?")) return;
  try {
    const data = await api("/api/books/" + bookId, { method: "DELETE" });
    showMessage(data.message, "success");
    refreshBooks();
  } catch (err) {
    showMessage(err.message, "error");
  }
}

// ----- Initial load -----
refreshBooks();
loadMembers();