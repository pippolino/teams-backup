(() => {
  "use strict";

  const archive = window.__TEAMS_ARCHIVE__;
  const state = { type: "all", query: "", selected: null };
  const list = document.querySelector("#chat-list");
  const main = document.querySelector("#main");
  const search = document.querySelector("#search");

  const typeLabels = { oneOnOne: "Individuale", group: "Gruppo", meeting: "Riunione" };
  const dateFormatter = new Intl.DateTimeFormat("it-IT", { dateStyle: "medium" });
  const timeFormatter = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });

  document.querySelector("#owner").textContent = archive.user.displayName || archive.user.userPrincipalName || "Backup locale";
  document.querySelector("#count-all").textContent = archive.chatCount;
  document.querySelector("#export-date").textContent = `Esportato ${formatDate(archive.exportedAt)}`;

  document.querySelectorAll(".filter").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".filter").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      state.type = button.dataset.type;
      renderList();
    });
  });

  search.addEventListener("input", () => {
    state.query = search.value.trim().toLocaleLowerCase("it");
    renderList();
  });

  function renderList() {
    list.replaceChildren();
    const chats = archive.chats.filter(matches);
    if (!chats.length) {
      const empty = element("p", "no-results", "Nessuna conversazione trovata.");
      list.append(empty);
      return;
    }
    chats.forEach((chat) => {
      const button = element("button", `chat-item${chat.id === state.selected ? " active" : ""}`);
      button.type = "button";
      button.setAttribute("role", "listitem");
      button.append(element("strong", "", chat.title));
      const details = element("small");
      details.append(element("span", "", typeLabels[chat.type] || chat.type), element("span", "", `${chat.messages.length} msg`));
      button.append(details);
      button.addEventListener("click", () => selectChat(chat));
      list.append(button);
    });
  }

  function matches(chat) {
    if (state.type !== "all" && chat.type !== state.type) return false;
    if (!state.query) return true;
    const memberText = chat.members.map((member) => `${member.displayName || ""} ${member.email || ""}`).join(" ");
    const messageText = chat.messages.map((message) => stripHtml(message.body?.content || "")).join(" ");
    return `${chat.title} ${memberText} ${messageText}`.toLocaleLowerCase("it").includes(state.query);
  }

  function selectChat(chat) {
    state.selected = chat.id;
    renderList();
    main.replaceChildren();
    const header = element("header", "conversation-header");
    header.append(element("div", "conversation-kicker", typeLabels[chat.type] || chat.type));
    header.append(element("h1", "", chat.title));
    const memberNames = chat.members.map((member) => member.displayName || member.email).filter(Boolean).join(" · ");
    header.append(element("div", "participants", memberNames || "Partecipanti non disponibili"));
    if (chat.webUrl) {
      const link = element("a", "teams-link", "Apri in Teams ↗");
      link.href = chat.webUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      header.append(link);
    }
    main.append(header);

    const messages = element("section", "messages");
    const groups = groupByDay(chat.messages);
    groups.forEach(({ day, items }) => {
      const section = element("section", "day");
      section.append(element("div", "day-label", day));
      const stream = element("div");
      items.forEach((message) => stream.append(renderMessage(message)));
      section.append(stream);
      messages.append(section);
    });
    if (!chat.messages.length) messages.append(element("p", "no-results", "Questa chat non contiene messaggi esportabili."));
    main.append(messages);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function renderMessage(message) {
    const wrapper = element("article", "message");
    const author = message.from?.user?.displayName || message.from?.application?.displayName || "Sistema";
    const meta = element("div", "message-meta");
    meta.append(element("strong", "", author));
    const time = element("time", "", formatTime(message.createdDateTime));
    time.dateTime = message.createdDateTime || "";
    meta.append(time);
    wrapper.append(meta);

    const body = element("div", message.messageType === "message" ? "message-body" : "system-message");
    body.innerHTML = message.body?.content || "";
    wrapper.append(body);
    if (message.reactions?.length) {
      const counts = {};
      message.reactions.forEach((reaction) => { counts[reaction.reactionType] = (counts[reaction.reactionType] || 0) + 1; });
      wrapper.append(element("div", "reactions", Object.entries(counts).map(([name, count]) => `${name} ${count}`).join(" · ")));
    }
    return wrapper;
  }

  function groupByDay(messages) {
    const groups = [];
    messages.forEach((message) => {
      const day = formatDate(message.createdDateTime);
      const current = groups.at(-1);
      if (!current || current.day !== day) groups.push({ day, items: [message] });
      else current.items.push(message);
    });
    return groups;
  }

  function element(tag, className = "", text = "") {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function formatDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.valueOf()) ? "Data sconosciuta" : dateFormatter.format(date);
  }

  function formatTime(value) {
    const date = new Date(value);
    return Number.isNaN(date.valueOf()) ? "" : timeFormatter.format(date);
  }

  function stripHtml(value) {
    const template = document.createElement("template");
    template.innerHTML = value;
    return template.content.textContent || "";
  }

  renderList();
})();
