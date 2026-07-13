import { GenLayerClient, Account } from 'genlayer-js';
import * as dotenv from 'dotenv';
import { executeOneshot } from './oneshot-executor';

dotenv.config();

const CONTRACT_ADDRESS = process.env.DCA_CONTRACT_ADDRESS || '0x1dC06EaDD445C82810bBe2Ead5564e878c899A4b';
const RPC_URL = process.env.GENLAYER_RPC_URL || 'https://studionet.genlayer.com';
const PRIVATE_KEY = process.env.ORCHESTRATOR_PRIVATE_KEY;

export async function runHeartbeat() {
  console.log('[Heartbeat] Connecting to Studionet at:', RPC_URL);
  const client = new GenLayerClient({ rpcUrl: RPC_URL });
  
  let executorAccount: Account | undefined = undefined;
  if (PRIVATE_KEY) {
    executorAccount = Account.fromPrivateKey(PRIVATE_KEY);
    console.log('[Heartbeat] Loaded executor account:', executorAccount.address);
  } else {
    console.warn('[Heartbeat] ORCHESTRATOR_PRIVATE_KEY not set. Write transactions will fail if signature is required.');
  }

  const currentTime = Math.floor(Date.now() / 1000);
  console.log('[Heartbeat] Running heartbeat at:', new Date(currentTime * 1000).toLocaleString());

  try {
    console.log('[Heartbeat] Polling due queue batch...');
    const rawDueBatch = await client.readContract({
      address: CONTRACT_ADDRESS,
      functionName: 'get_due_batch',
      args: [currentTime]
    });

    const duePolicies: string[] = JSON.parse(rawDueBatch);
    console.log(`[Heartbeat] Found ${duePolicies.length} policies due for evaluation.`);

    for (const policyId of duePolicies) {
      console.log(`[Heartbeat] Processing policy: ${policyId}`);
      try {
        if (!executorAccount) {
          throw new Error('Cannot execute DCA step: ORCHESTRATOR_PRIVATE_KEY is missing.');
        }

        console.log(`[Heartbeat] Invoking execute_dca_step for ${policyId}...`);
        const txHash = await client.writeContract({
          address: CONTRACT_ADDRESS,
          functionName: 'execute_dca_step',
          args: [policyId, currentTime],
          account: executorAccount
        });

        console.log(`[Heartbeat] execute_dca_step TX submitted: ${txHash}. Waiting for transaction receipt...`);
        const receipt = await client.waitForTransactionReceipt({ hash: txHash });
        console.log(`[Heartbeat] Transaction finalized in block ${receipt.blockNumber}.`);

        // Retrieve updated interval and decision details to see if instructions were generated
        const rawPolicy = await client.readContract({
          address: CONTRACT_ADDRESS,
          functionName: 'get_policy',
          args: [policyId]
        });
        const policy = JSON.parse(rawPolicy);
        console.log(`[Heartbeat] Policy ${policyId} status is now: ${policy.status}`);
        
        // Poll latest queue/interval to check for authorized instructions
        // Normally we scan event logs, but we can also query contract state views
        // If policy is active, we checks latest interval execution state
        const rawQueue = await client.readContract({
          address: CONTRACT_ADDRESS,
          functionName: 'get_queue',
          args: []
        });
        console.log('[Heartbeat] Queue state:', rawQueue);

      } catch (policyError: any) {
        console.error(`[Heartbeat] Error processing policy ${policyId}:`, policyError);
      }
    }

    // In addition to running executions, scan for open authorized execution instructions
    // and execute the actual swaps on Uniswap/Relays via Oneshot Executor
    console.log('[Heartbeat] Scanning for pending execution instructions...');
    await executeOneshot(client, executorAccount);

  } catch (error) {
    console.error('[Heartbeat] Loop execution error:', error);
    throw error;
  }
}

if (require.main === module) {
  runHeartbeat().then(() => {
    console.log('[Heartbeat] Finished execution cycle successfully.');
    process.exit(0);
  }).catch((err) => {
    console.error('[Heartbeat] Finished execution cycle with error:', err);
    process.exit(1);
  });
}
