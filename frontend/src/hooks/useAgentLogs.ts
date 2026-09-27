import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'

import { apiFetch } from '@/utils/api'

export const agentLogSchema = z.object({
  id: z.number(),
  question: z.string(),
  answer: z.string(),
  created_at: z.string(),
  like_count: z.number(),
})

export type AgentLog = z.infer<typeof agentLogSchema>

export const agentLogListSchema = z.array(agentLogSchema)

export const agentLogKeys = {
  all: ['agent-logs'] as const,
  list: () => [...agentLogKeys.all, 'list'] as const,
}

async function fetchAgentLogs(): Promise<AgentLog[]> {
  const data = await apiFetch<unknown>('/agent-logs')
  return agentLogListSchema.parse(data)
}

export function useAgentLogs() {
  return useQuery({
    queryKey: agentLogKeys.list(),
    queryFn: fetchAgentLogs,
  })
}
