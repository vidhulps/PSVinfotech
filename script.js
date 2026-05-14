// ═══════════════════════════════════════
// FIREBASE IMPORTS
// ═══════════════════════════════════════

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";

import {
  getFirestore,
  collection,
  addDoc
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";


// ═══════════════════════════════════════
// FIREBASE CONFIG
// ═══════════════════════════════════════

const firebaseConfig = {
  apiKey: "AIzaSyBmXXhf6czGpFH2TRT0nCDr3r5BgD6g40U",
  authDomain: "psvinfotech-a7dd1.firebaseapp.com",
  projectId: "psvinfotech-a7dd1",
  storageBucket: "psvinfotech-a7dd1.firebasestorage.app",
  messagingSenderId: "222039714267",
  appId: "1:222039714267:web:d2ca5dd93d1023494c9ffe",
  measurementId: "G-BE0B2RF21V"
};


// ═══════════════════════════════════════
// INITIALIZE FIREBASE
// ═══════════════════════════════════════

const app = initializeApp(firebaseConfig);

const db = getFirestore(app);


// ═══════════════════════════════════════
// GSAP ANIMATIONS
// ═══════════════════════════════════════

gsap.registerPlugin(ScrollTrigger);

gsap.from(".hero-title", {
  y: 100,
  opacity: 0,
  duration: 1.5
});

gsap.from(".hero-subtitle", {
  y: 50,
  opacity: 0,
  duration: 1.5,
  delay: 0.3
});

gsap.from(".hero-cta", {
  y: 50,
  opacity: 0,
  duration: 1.5,
  delay: 0.5
});


// ═══════════════════════════════════════
// THREE.JS BACKGROUND
// ═══════════════════════════════════════

const canvas = document.getElementById("bg-canvas");

const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(
  75,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);

const renderer = new THREE.WebGLRenderer({
  canvas,
  alpha: true
});

renderer.setSize(window.innerWidth, window.innerHeight);

camera.position.z = 5;

const geometry = new THREE.TorusKnotGeometry(1, 0.3, 128, 16);

const material = new THREE.MeshBasicMaterial({
  color: 0x00bfff,
  wireframe: true
});

const torus = new THREE.Mesh(geometry, material);

scene.add(torus);

function animate() {

  requestAnimationFrame(animate);

  torus.rotation.x += 0.003;
  torus.rotation.y += 0.005;

  renderer.render(scene, camera);

}

animate();


// ═══════════════════════════════════════
// RESPONSIVE CANVAS
// ═══════════════════════════════════════

window.addEventListener("resize", () => {

  camera.aspect = window.innerWidth / window.innerHeight;

  camera.updateProjectionMatrix();

  renderer.setSize(window.innerWidth, window.innerHeight);

});


// ═══════════════════════════════════════
// CHATBOT
// ═══════════════════════════════════════

const chatToggle = document.getElementById("chat-toggle");

const chatWindow = document.getElementById("chat-window");

chatToggle.addEventListener("click", () => {

  chatWindow.classList.toggle("active");

});

const chatInput = document.getElementById("chat-input");

const chatMessages = document.getElementById("chat-messages");

document.getElementById("chat-send")
  .addEventListener("click", sendMessage);

function sendMessage() {

  const message = chatInput.value.trim();

  if (!message) return;

  const userMsg = `
    <div class="message user-message">
      <div class="msg-bubble">${message}</div>
    </div>
  `;

  chatMessages.innerHTML += userMsg;

  chatInput.value = "";

  setTimeout(() => {

    const botMsg = `
      <div class="message bot-message">
        <div class="msg-bubble">
          Thanks for contacting PSV Infotech 🚀<br>
          Our AI assistant will help you soon.
        </div>
      </div>
    `;

    chatMessages.innerHTML += botMsg;

    chatMessages.scrollTop = chatMessages.scrollHeight;

  }, 1000);

}


// ═══════════════════════════════════════
// CONTACT FORM + FIREBASE
// ═══════════════════════════════════════

const form = document.getElementById("contact-form");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = document.getElementById("name").value;
  const email = document.getElementById("email").value;
  const phone = document.getElementById("phone").value;
  const service = document.getElementById("service").value;
  const message = document.getElementById("message").value;

  try {
    await addDoc(collection(db, "contacts"), {
      name,
      email,
      phone,
      service,
      message,
      createdAt: new Date()
    });

    alert("Message Sent Successfully ✅");
    form.reset();

  } catch (error) {
    console.error("Error Sending Message:", error);
    alert("Error Sending Message");
  }
});


// ═══════════════════════════════════════
// SCROLL TO TOP
// ═══════════════════════════════════════

const scrollBtn = document.getElementById("scroll-top");

window.addEventListener("scroll", () => {

  if (window.scrollY > 300) {

    scrollBtn.style.display = "flex";

  } else {

    scrollBtn.style.display = "none";

  }

});

scrollBtn.addEventListener("click", () => {

  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });

});


// ═══════════════════════════════════════
// COUNTER ANIMATION
// ═══════════════════════════════════════

const counters = document.querySelectorAll(".stat-num");

counters.forEach(counter => {

  const updateCounter = () => {

    const target = +counter.getAttribute("data-target");

    const current = +counter.innerText;

    const increment = target / 100;

    if (current < target) {

      counter.innerText = Math.ceil(current + increment);

      setTimeout(updateCounter, 20);

    } else {

      counter.innerText = target;

    }

  };

  updateCounter();

});