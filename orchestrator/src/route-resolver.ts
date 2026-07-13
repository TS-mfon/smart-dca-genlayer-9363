import { EthersRouteQuote } from './types';

// A mock router simulating a swap query
export async function resolveRouteAndQuote(
  fundingAsset: string,
  targetAsset: string,
  amount: number,
  approvedVenues: string[],
  slippageBps: number
): Promise<EthersRouteQuote> {
  console.log(`[Router] Resolving route: ${amount} ${fundingAsset} -> ${targetAsset} across venues: ${approvedVenues.join(', ')}`);
  
  // Simulate 500ms API latency
  await new Promise(resolve => setTimeout(resolve, 500));
  
  if (amount <= 0) {
    throw new Error('Invalid input amount');
  }

  // Assume a fixed swap rate for the POC (e.g. 1 USDC = 0.0003 ETH)
  const rate = targetAsset.toUpperCase() === 'ETH' ? 0.0003 : 3300;
  const expectedOutput = amount * rate;
  const slippageMultiplier = (10000 - slippageBps) / 10000;
  const minOutput = Math.floor(expectedOutput * slippageMultiplier * 1000000) / 1000000;
  const actualOutput = Math.floor(expectedOutput * 0.995 * 1000000) / 1000000; // slightly less than expected due to price impact

  if (actualOutput < minOutput) {
    throw new Error('Slippage tolerance exceeded during quote simulation');
  }

  return {
    txHash: '0x' + Array.from({length: 64}, () => Math.floor(Math.random()*16).toString(16)).join(''),
    venue: approvedVenues[0] || 'Uniswap_V3',
    expectedOutput: actualOutput,
    minOutput: minOutput,
    actualOutput: actualOutput,
    gasUsed: 85000,
    blockNumber: 19827394
  };
}
