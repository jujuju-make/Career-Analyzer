"use client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiError {
  detail: string;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // ─── Resume ───
  async uploadResume(file: File) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/api/v1/resume/upload`, {
      method: "POST",
      body: form,
    });
    return handleResponse<{ resume_id: string; filename: string }>(res);
  },

  // ─── JD ───
  async uploadJdImage(file: File) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/api/v1/jd/upload-image`, {
      method: "POST",
      body: form,
    });
    return handleResponse<{ jd_id: string; text: string }>(res);
  },

  async uploadJdPdf(file: File) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/api/v1/jd/upload-pdf`, {
      method: "POST",
      body: form,
    });
    return handleResponse<{ jd_id: string; text: string }>(res);
  },

  // ─── Analysis ───
  async startAnalysis(resumeId: string, jdInput: string, targetPosition: string) {
    const res = await fetch(`${API_BASE}/api/v1/career/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume_id: resumeId,
        job_description: jdInput,
        target_position: targetPosition,
      }),
    });
    return handleResponse<{ task_id: string; status: string }>(res);
  },

  async getAnalysisResult(taskId: string) {
    const res = await fetch(`${API_BASE}/api/v1/career/result/${taskId}`);
    return handleResponse<{
      task_id: string;
      status: string;
      resume_structured: any;
      jd_analysis: any;
      gap_analysis: string;
      optimition: string;
      project_recommendations: any[];
    }>(res);
  },

  // ─── Learning ───
  async getProjectRecommendations() {
    const res = await fetch(`${API_BASE}/api/v1/learning/recommend-projects`);
    return handleResponse<any[]>(res);
  },

  async getResumeOptimize() {
    const res = await fetch(`${API_BASE}/api/v1/learning/resume-optimize`);
    return handleResponse<{ optimition: string }>(res);
  },

  // ─── Interview ───
  async startInterview(taskId: string) {
    const res = await fetch(`${API_BASE}/api/v1/interview/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId }),
    });
    return handleResponse<{
      session_id: string;
      task_id: string;
      round_name: string;
      current_question: {
        question: string;
        question_index: number;
        total: number;
        module_name: string;
        module_label: string;
        is_follow_up: boolean;
      };
    }>(res);
  },

  async submitAnswer(sessionId: string, answer: string) {
    const res = await fetch(`${API_BASE}/api/v1/interview/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, answer }),
    });
    return handleResponse<{
      correct: string;
      score: number;
      feedback: string;
      is_follow_up: boolean;
      follow_up_question: string | null;
      next_question: {
        question: string;
        question_index: number;
        total: number;
        module_name: string;
        module_label: string;
        is_follow_up: boolean;
      } | null;
      interview_over: boolean;
      final_result: any;
    }>(res);
  },

  async getSessionStatus(sessionId: string) {
    const res = await fetch(`${API_BASE}/api/v1/interview/session/${sessionId}`);
    return handleResponse<any>(res);
  },

  async getInterviewResult(taskId: string) {
    const res = await fetch(`${API_BASE}/api/v1/interview/result/${taskId}`);
    return handleResponse<any>(res);
  },
};
