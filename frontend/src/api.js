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

export async function savePartial(payload) {
  // payload: { name?, email, answers, step }
  const { data } = await http.post("/quiz/partial", payload);
  return data;
}

export async function sendReminders(token) {
  const { data } = await http.post("/admin/send-reminders", {}, { headers: { "X-Admin-Token": token } });
  return data; // { reminders_sent, pending }
}

export async function emailResult(resultId) {
  const { data } = await http.post(`/results/${resultId}/email`);
  return data; // { status, sent_to }
}

export async function getResult(resultId) {
  const { data } = await http.get(`/results/${resultId}`);
  return data; // { result_id, scored }
}

export async function getAdminLeads(token, params = {}) {
  const { data } = await http.get("/admin/leads", { headers: { "X-Admin-Token": token }, params });
  return data; // { total, leads }
}

export async function getAdminInsights(token, params = {}) {
  const { data } = await http.get("/admin/insights", { headers: { "X-Admin-Token": token }, params });
  return data; // { total_results, emails_sent, by_card, by_goal, incomplete_sessions }
}

export function leadsCsvUrl(token, params = {}) {
  const q = new URLSearchParams({ token, ...params }).toString();
  return `${API}/admin/leads.csv?${q}`;
}

export async function compareCards(ids) {
  const { data } = await http.post("/cards/compare", { ids });
  return data; // [cards]
}
