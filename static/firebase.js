import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyDod8d71cZxTkfqO2hcGImPZJDpm5hW-no",
  authDomain: "trustshield-c11e4.firebaseapp.com",
  projectId: "trustshield-c11e4",
  storageBucket: "trustshield-c11e4.appspot.com",
  messagingSenderId: "560088879448",
  appId: "1:560088879448:web:eb0559ad11bc636b57952d"
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
