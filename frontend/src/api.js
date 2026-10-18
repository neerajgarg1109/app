import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const http = axios.create({ baseURL: API });

export async function getCards() {
  const { data } = await http.get("/cards");
  return data;
}

export async function submitQuiz(answers, lead) {
  const { data } = await http.post("/quiz/submit", lead ? { answers, lead } : { answers });
  return data; // { result_id, scored }
}

export async function attachResultLead(resultId, lead) {
  const { data } = await http.post(`/results/${resultId}/lead`, lead);
  return data;
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

export async function getAdminCards(token) {
  const { data } = await http.get("/admin/cards", { headers: { "X-Admin-Token": token } });
  return data; // { cards }
}

export async function createAdminCard(token, card) {
  const { data } = await http.post("/admin/cards", card, { headers: { "X-Admin-Token": token } });
  return data;
}

export async function updateAdminCard(token, cardId, card) {
  const { data } = await http.put(`/admin/cards/${encodeURIComponent(cardId)}`, card, { headers: { "X-Admin-Token": token } });
  return data;
}

export async function publishAdminCard(token, cardId) {
  const { data } = await http.post(`/admin/cards/${encodeURIComponent(cardId)}/publish`, {}, { headers: { "X-Admin-Token": token } });
  return data;
}

export async function discardAdminCardDraft(token, cardId) {
  const { data } = await http.delete(`/admin/cards/${encodeURIComponent(cardId)}/draft`, { headers: { "X-Admin-Token": token } });
  return data;
}

export async function getAdminCardHistory(token, cardId) {
  const { data } = await http.get(`/admin/cards/${encodeURIComponent(cardId)}/history`, { headers: { "X-Admin-Token": token } });
  return data;
}

export async function rollbackAdminCard(token, cardId, versionId) {
  const { data } = await http.post(`/admin/cards/${encodeURIComponent(cardId)}/rollback/${encodeURIComponent(versionId)}`, {}, { headers: { "X-Admin-Token": token } });
  return data;
}

export async function archiveAdminCard(token, cardId, restore = false) {
  const { data } = await http.post(`/admin/cards/${encodeURIComponent(cardId)}/${restore ? "restore" : "archive"}`, {}, { headers: { "X-Admin-Token": token } });
  return data;
}

export async function previewAdminCardRecommendation(token, cardId, answers) {
  const { data } = await http.post(`/admin/cards/${encodeURIComponent(cardId)}/recommendation-preview`, { answers }, { headers: { "X-Admin-Token": token } });
  return data;
}

export async function exportAdminCards(token, format) {
  const { data } = await http.get("/admin/cards-export", { headers: { "X-Admin-Token": token }, params: { format }, responseType: format === "csv" ? "blob" : "json" });
  return data;
}

export async function importAdminCards(token, cards, dryRun = true) {
  const { data } = await http.post("/admin/cards-import", cards, { headers: { "X-Admin-Token": token }, params: { dry_run: dryRun } });
  return data;
}

export async function updateAdminCardApplyLink(token, cardId, configuration) {
  const { data } = await http.put(
    `/admin/cards/${encodeURIComponent(cardId)}/apply-link`,
    configuration ? {
      apply_url: configuration.url || null,
      partner_name: configuration.partner || null,
      campaign_id: configuration.campaign || null,
      tracking_id: configuration.tracking || null,
      status: configuration.status || "testing",
      expected_payout: configuration.payout === "" || configuration.payout == null ? null : Number(configuration.payout),
    } : { apply_url: null },
    { headers: { "X-Admin-Token": token } },
  );
  return data;
}

export function leadsCsvUrl(token, params = {}) {
  const q = new URLSearchParams({ token, ...params }).toString();
  return `${API}/admin/leads.csv?${q}`;
}

export async function compareCards(ids) {
  const { data } = await http.post("/cards/compare", { ids });
  return data; // [cards]
}

export async function calculateCardValue(spending) {
  const { data } = await http.post("/tools/value-calculator", spending);
  return data;
}

export async function subscribeCardAlerts(subscription) {
  const { data } = await http.post("/card-alerts", subscription);
  return data;
}

export async function trackApplyClick(cardId, resultId) {
  const { data } = await http.post(`/cards/${encodeURIComponent(cardId)}/apply-click`, { result_id: resultId || null });
  return data;
}

export async function reportCardInformation(cardId, issue, email) {
  const { data } = await http.post(`/cards/${encodeURIComponent(cardId)}/report`, { issue, email: email || null });
  return data;
}

export async function scheduleReviewFollowup(cardId, email, resultId) {
  const { data } = await http.post(`/cards/${encodeURIComponent(cardId)}/review-followup`, { email, result_id: resultId || null, review_consent: true });
  return data;
}

export async function submitExperienceFeedback(rating, feedback, resultId, cardId) {
  const { data } = await http.post("/experience-feedback", {
    rating,
    feedback: feedback.trim() || null,
    result_id: resultId || null,
    card_id: cardId || null,
  });
  return data;
}

export async function trackProductEvent(event, sessionId, resultId = null, metadata = {}) {
  const { data } = await http.post("/product-events", {
    event,
    session_id: sessionId,
    result_id: resultId,
    ...metadata,
  });
  return data;
}

export async function getCommunityRating(cardId) {
  const { data } = await http.get(`/cards/${encodeURIComponent(cardId)}/community-rating`);
  return data;
}

export async function getReviewInvitation(token) {
  const { data } = await http.get(`/reviews/invite/${encodeURIComponent(token)}`);
  return data;
}

export async function submitCardholderReview(token, review) {
  const { data } = await http.post(`/reviews/invite/${encodeURIComponent(token)}`, review);
  return data;
}

export async function getAdminCardReviews(token) {
  const { data } = await http.get("/admin/card-reviews", { headers: { "X-Admin-Token": token } });
  return data;
}

export async function moderateAdminCardReview(token, reviewId, status) {
  const { data } = await http.put(`/admin/card-reviews/${encodeURIComponent(reviewId)}`, { status }, { headers: { "X-Admin-Token": token } });
  return data;
}

export async function sendAdminReviewReminders(token) {
  const { data } = await http.post("/admin/send-review-reminders", {}, { headers: { "X-Admin-Token": token } });
  return data;
}
