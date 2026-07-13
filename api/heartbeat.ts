import { runHeartbeat } from '../orchestrator/src/heartbeat';
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    console.log('[Cron] Heartbeat triggered');
    await runHeartbeat();
    return res.status(200).json({ success: true, message: 'Heartbeat executed successfully.' });
  } catch (error: any) {
    console.error('[Cron] Heartbeat failed:', error);
    return res.status(500).json({ success: false, error: error.message });
  }
}