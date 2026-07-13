import { GenLayerClient, Account } from 'genlayer-js';
import { resolveRouteAndQuote } from './route-resolver';

const CONTRACT_ADDRESS = process.env.DCA_CONTRACT_ADDRESS || '0x1dC06EaDD445C82810bBe2Ead5564e878c899A4b';

export async function executeOneshot(client: GenLayerClient, account?: Account) {
  if (!account) {
    console.warn('[Executor] No signer account provided. Skipping execution settlement.');
    return;
  }

  console.log('[Executor] Polling pending instructions from contract...');
  
  // For this mock-up / POC flow, the orchestrator retrieves instructions by scanning intervals or queue
  // In production, we listen to the contract's "ExecutionAuthorized" event.
  // Since event subscriptions might be transient, we can also iterate through known active policies
  // and pull their latest intervals. Here we mock the checking of POL-1 to POL-10 intervals for brevity:
  for (let i = 1; i <= 10; i++) {
    const policyId = `POL-${i}`;
    try {
      const rawPolicy = await client.readContract({
        address: CONTRACT_ADDRESS,
        functionName: 'get_policy',
        args: [policyId]
      });
      const policy = JSON.parse(rawPolicy);
      if (!policy.policy_id) continue; // Policy doesn't exist

      // Check the latest interval
      // For POC, we construct the interval ID matching the counter
      // In production, we'd query a registry or events
      const intervalId = `INT-${policyId}-1`; 
      const rawInterval = await client.readContract({
        address: CONTRACT_ADDRESS,
        functionName: 'get_interval',
        args: [intervalId]
      });
      const interval = JSON.parse(rawInterval);
      
      if (interval.execution_state === 'ExecutionAuthorized') {
        console.log(`[Executor] Found authorized execution step on ${intervalId}.`);
        
        // Get instruction details
        const instructionId = `INST-${intervalId}-1`;
        const rawInstruction = await client.readContract({
          address: CONTRACT_ADDRESS,
          functionName: 'get_instruction',
          args: [instructionId]
        });
        const inst = JSON.parse(rawInstruction);
        
        if (!inst.instruction_id) {
          console.warn(`[Executor] Instruction ${instructionId} not found.`);
          continue;
        }

        console.log(`[Executor] Executing route resolution for target asset: ${inst.target_asset} with ${inst.spend_amount} ${inst.funding_asset}`);
        
        try {
          const route = await resolveRouteAndQuote(
            inst.funding_asset,
            inst.target_asset,
            inst.spend_amount,
            inst.approved_venues,
            inst.slippage_bound
          );
          
          console.log(`[Executor] Route resolved. Executing settlement on chain...`, route);
          
          // Submit record_settlement back to GenLayer contract
          const txHash = await client.writeContract({
            address: CONTRACT_ADDRESS,
            functionName: 'record_settlement',
            args: [
              inst.instruction_id,
              route.txHash,
              route.venue,
              inst.spend_amount,
              route.minOutput,
              route.actualOutput,
              route.gasUsed,
              route.blockNumber,
              route.blockNumber,
              Math.floor(Date.now() / 1000)
            ],
            account: account
          });
          
          console.log(`[Executor] Settlement registered in TX: ${txHash}`);
          await client.waitForTransactionReceipt({ hash: txHash });
          console.log(`[Executor] Instruction ${inst.instruction_id} settled successfully.`);
          
        } catch (execError: any) {
          console.error(`[Executor] Execution failed for instruction ${inst.instruction_id}:`, execError);
          // Record failure on chain to unlock or block policy
          const txHash = await client.writeContract({
            address: CONTRACT_ADDRESS,
            functionName: 'record_failure',
            args: [
              inst.instruction_id,
              'ExecutionFailed',
              execError.message || 'Swap execution reverted',
              'Orchestrator',
              true, // retriable
              Math.floor(Date.now() / 1000)
            ],
            account: account
          });
          console.log(`[Executor] Failure registered on-chain: ${txHash}`);
          await client.waitForTransactionReceipt({ hash: txHash });
        }
      }
    } catch (e) {
      // Policy or interval might not exist yet, skip silently
    }
  }
}
