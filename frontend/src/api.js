import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const http = axios.create({ baseURL: API });

export async function getCards() {
  const { data } = await http.get("/cards");
  return data;
}

export async function submitQuiz(answers, lead) {
  const { data } = await http.post("/quiz/submit", { answers, lead });
  return data; // { result_id, scored }
}

export async function emailResult(resultId) {
  const { data } = await http.post(`/results/${resultId}/email`);
  return data; // { status, sent_to }
}

export async function getResult(resultId) {
  const { data } = await http.get(`/results/${resultId}`);
  return data; // { result_id, scored }
}

export async function getAdminLeads(token) {
  const { data } = await http.get("/admin/leads", { headers: { "X-Admin-Token": token } });
  return data; // { total, leads }
}

export async function compareCards(ids) {
  const { data } = await http.post("/cards/compare", { ids });
  return data; // [cards]
}
