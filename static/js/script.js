/* =========================================================
   SMARTASSIST CHAT
   ========================================================= */

const root = document.getElementById("appRoot");

const messages =
  document.getElementById("messages");

const form =
  document.getElementById("chatForm");

const input =
  document.getElementById("messageInput");

const sendButton =
  document.getElementById("sendButton");

const clearButton =
  document.getElementById("clearChat");

const charCount =
  document.getElementById("charCount");

const quickActions =
  document.getElementById("quickActions");


/* =========================================================
   HELPERS
   ========================================================= */

function currentTime() {

  return new Intl.DateTimeFormat([], {
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date());

}


function setThinking(state) {

  root.classList.toggle(
    "is-thinking",
    state
  );

  sendButton.disabled = state;

}


function scrollMessages() {

  requestAnimationFrame(() => {

    messages.scrollTo({
      top: messages.scrollHeight,
      behavior: "smooth"
    });

  });

}


function updateCharacterCount() {

  charCount.textContent =
    `${input.value.length} / 2000`;

}


function resizeInput() {

  input.style.height = "auto";

  input.style.height =
    `${Math.min(
      input.scrollHeight,
      110
    )}px`;

}


function activateConversation() {

  root.classList.add(
    "has-conversation"
  );

}


/* =========================================================
   ADD USER MESSAGE
   ========================================================= */

function addUserMessage(text) {

  activateConversation();

  const article =
    document.createElement("article");

  article.className =
    "message user-message";

  article.innerHTML = `

    <div class="message-meta">

      <span>
        You
      </span>

      <time>
        ${currentTime()}
      </time>

    </div>

    <div class="message-bubble"></div>

  `;

  article
    .querySelector(".message-bubble")
    .textContent = text;

  messages.appendChild(article);

  scrollMessages();

}


/* =========================================================
   ADD ASSISTANT MESSAGE
   ========================================================= */

function addAssistantMessage(text) {

  const article =
    document.createElement("article");

  article.className =
    "message assistant-message";

  article.innerHTML = `

    <div class="message-meta">

      <div class="message-mini-orb">
        <span></span>
      </div>

      <span>
        SmartAssist
      </span>

      <time>
        ${currentTime()}
      </time>

    </div>

    <div class="message-bubble"></div>

  `;

  article
    .querySelector(".message-bubble")
    .textContent = text;

  messages.appendChild(article);

  scrollMessages();

}


/* =========================================================
   TYPING INDICATOR
   ========================================================= */

function showTyping() {

  hideTyping();

  const article =
    document.createElement("article");

  article.id =
    "typingIndicator";

  article.className =
    "message assistant-message";

  article.innerHTML = `

    <div class="message-meta">

      <div class="message-mini-orb">
        <span></span>
      </div>

      <span>
        SmartAssist
      </span>

      <time>
        thinking
      </time>

    </div>

    <div class="message-bubble">

      <span class="typing-dots">
        <i></i>
        <i></i>
        <i></i>
      </span>

    </div>

  `;

  messages.appendChild(article);

  scrollMessages();

}


function hideTyping() {

  const typing =
    document.getElementById(
      "typingIndicator"
    );

  if (typing) {
    typing.remove();
  }

}


/* =========================================================
   SEND MESSAGE
   ========================================================= */

async function sendMessage(rawText) {

  const text =
    rawText.trim();

  if (!text) {
    return;
  }

  if (sendButton.disabled) {
    return;
  }

  addUserMessage(text);

  input.value = "";

  updateCharacterCount();

  resizeInput();

  setThinking(true);

  showTyping();

  try {

    const response =
      await fetch(
        "/chat",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({
            message: text
          })
        }
      );


    let data = {};

    try {

      data =
        await response.json();

    } catch {

      data = {};

    }


    hideTyping();


    if (
      !response.ok ||
      !data.ok
    ) {

      addAssistantMessage(
        data.error ||
        "Something went wrong while processing your request. Please try again."
      );

      return;

    }


    addAssistantMessage(
      data.response ||
      "I couldn't generate a response right now."
    );


  } catch (error) {

    console.error(
      "SmartAssist request failed:",
      error
    );

    hideTyping();

    addAssistantMessage(
      "I couldn't connect to SmartAssist. Please check that the Flask server and Groq API are running."
    );

  } finally {

    setThinking(false);

    input.focus();

  }

}


/* =========================================================
   FORM
   ========================================================= */

form.addEventListener(
  "submit",
  (event) => {

    event.preventDefault();

    sendMessage(
      input.value
    );

  }
);


/* =========================================================
   TEXTAREA
   ========================================================= */

input.addEventListener(
  "input",
  () => {

    updateCharacterCount();

    resizeInput();

  }
);


input.addEventListener(
  "keydown",
  (event) => {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      form.requestSubmit();

    }

  }
);


/* =========================================================
   QUICK PROMPTS
   ========================================================= */

quickActions.addEventListener(
  "click",
  (event) => {

    const button =
      event.target.closest(
        "button"
      );

    if (!button) {
      return;
    }

    const message =
      button.dataset.message;

    if (!message) {
      return;
    }

    sendMessage(message);

  }
);


/* =========================================================
   NEW CONVERSATION
   ========================================================= */

clearButton.addEventListener(
  "click",
  async () => {

    try {

      await fetch(
        "/clear-chat",
        {
          method: "POST"
        }
      );

    } catch (error) {

      console.warn(
        "Server session could not be cleared:",
        error
      );

    }


    messages.innerHTML = `

      <article class="message assistant-message">

        <div class="message-meta">

          <div class="message-mini-orb">
            <span></span>
          </div>

          <span>
            SmartAssist
          </span>

          <time>
            now
          </time>

        </div>

        <div class="message-bubble">

          Hello! I'm SmartAssist.
          What can I help you with?

        </div>

      </article>

    `;


    root.classList.remove(
      "has-conversation",
      "is-thinking"
    );


    input.value = "";

    updateCharacterCount();

    resizeInput();

    input.focus();

  }
);


/* =========================================================
   INIT
   ========================================================= */

updateCharacterCount();

resizeInput();

input.focus();