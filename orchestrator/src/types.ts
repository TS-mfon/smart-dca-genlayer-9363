export interface EthersRouteQuote {
  txHash: string;
  venue: string;
  expectedOutput: number;
  minOutput: number;
  actualOutput: number;
  gasUsed: number;
  blockNumber: number;
}
