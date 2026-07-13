# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from dataclasses import dataclass, field
import json

@allow_storage
@dataclass
class Policy:
    policy_id: str
    owner_wallet: str
    delegated_executor_wallet: str
    policy_version: int
    status: str  # "Active", "Paused", "Blocked", "Rejected", "Cancelled", "Historical"
    funding_asset: str  # USDC, etc.
    target_asset_constraints: str  # allowlisted constraints representation (e.g. JSON string)
    cadence_definition: int  # interval in seconds
    nominal_spend_amount: int  # spend amount per interval
    interval_spend_cap: int
    rolling_spend_cap: int
    execution_window_rule: int  # allowed delay in seconds
    slippage_rule: int  # basis points
    approved_venue_constraints: list[str]
    ai_strategy_profile: str
    created_at: int
    updated_at: int
    last_evaluated_at: int
    last_success_at: int
    next_due_at: int
    delegation_descriptor_id: str
    block_reason: str
    reject_reason: str

@allow_storage
@dataclass
class DelegationDescriptor:
    descriptor_id: str
    delegator_wallet: str
    delegate_wallet: str
    token_scope: str
    per_period_spend_limit: int
    active_period_definition: int
    expiry: int
    expected_revocation_model: str
    last_verified_at: int
    last_verification_result: str

@allow_storage
@dataclass
class QueueEntry:
    queue_entry_id: str
    policy_id: str
    active_membership: bool
    next_due_at: int
    retry_due_at: int
    tie_break_key: str
    traversal_metadata: str
    quarantine_flag: bool
    quarantine_reason: str
    last_pointer_visit_at: int

@allow_storage
@dataclass
class Interval:
    interval_id: str
    policy_id: str
    policy_version: int
    scheduled_due_at: int
    evaluation_state: str  # "Scheduled", "Due", "PrecheckFailed", "ReasoningInProgress", etc.
    execution_state: str  # "ExecutionAuthorized", "ExecutionPending", "IncludedUnconfirmed", "ConfirmedSuccess", "FailedRetriable", "FailedTerminal", "Closed"
    attempt_count: int
    last_failure_class: str
    retry_state: str
    terminal_outcome: str  # "success", "failure", "skip", "reject", ""
    opened_at: int
    closed_at: int

@allow_storage
@dataclass
class DecisionArtifact:
    decision_id: str
    policy_id: str
    policy_version: int
    interval_id: str
    verdict: str  # "BUY", "SKIP", "REJECT"
    selected_asset: str
    approved_spend_amount: int
    rationale_summary: str
    factor_summary: str
    evidence_reference_set: list[str]
    confidence_score: int
    safety_flags: list[str]
    decision_hash: str
    consensus_completed_at: int

@allow_storage
@dataclass
class ExecutionInstruction:
    instruction_id: str
    decision_id: str
    policy_id: str
    interval_id: str
    funding_asset: str
    spend_amount: int
    target_asset: str
    approved_venues: list[str]
    slippage_bound: int
    instruction_expiry: int
    idempotency_key: str
    validation_snapshot_reference: str

@allow_storage
@dataclass
class ExecutionAttempt:
    attempt_id: str
    instruction_id: str
    retry_ordinal: int
    local_validation_result: str
    bundler_submission_result: str
    bundler_reference: str
    transaction_hash: str
    lifecycle_state: str  # "Created", "LocallyValidated", "SubmissionPending", "BundlerAccepted", "OnchainPending", "Included", "Confirmed", "Reverted", "TimedOutUncertain", "Superseded", "FinalizedRecorded"
    started_at: int
    updated_at: int
    terminal_result: str
    failure_class: str

@allow_storage
@dataclass
class SettlementRecord:
    instruction_id: str
    transaction_hash: str
    venue: str
    quoted_input_amount: int
    quoted_min_output: int
    actual_output_amount: int
    gas_used: int
    inclusion_block: int
    confirmation_block: int
    settled_at: int
    settlement_status: str

@allow_storage
@dataclass
class FailureRecord:
    failure_id: str
    policy_id: str
    interval_id: str
    instruction_id: str
    layer: str
    failure_class: str
    cause: str
    detected_by: str
    retriable: bool
    retry_policy_reference: str
    recovery_requirement: str
    scope_of_impact: str

@allow_storage
@dataclass
class ProtocolConfig:
    config_version: int
    pause_mode: bool
    emergency_stop: bool
    supported_assets: list[str]
    target_asset_allowlist_policy: str
    target_asset_denylist: list[str]
    approved_venues: list[str]
    approved_data_sources: list[str]
    confirmation_threshold: int
    batch_limit: int
    retry_policies: str  # JSON representation of retry rules
    quote_validity_bounds: int
    gas_policy: str  # JSON representation of gas policies
    queue_integrity_policy: str

class DcaSystem(gl.Contract):
    owner: Address
    config: ProtocolConfig
    policies: TreeMap[str, Policy]
    delegations: TreeMap[str, DelegationDescriptor]
    intervals: TreeMap[str, Interval]
    decisions: TreeMap[str, DecisionArtifact]
    instructions: TreeMap[str, ExecutionInstruction]
    attempts: TreeMap[str, ExecutionAttempt]
    settlements: TreeMap[str, SettlementRecord]
    failures: TreeMap[str, FailureRecord]
    queue: DynArray[QueueEntry]
    policy_counter: int
    interval_counter: int
    decision_counter: int
    instruction_counter: int
    attempt_counter: int
    failure_counter: int

    PolicyRegistered = gl.Event("PolicyRegistered", {"policy_id": "str", "owner_wallet": "str"})
    PolicyUpdated = gl.Event("PolicyUpdated", {"policy_id": "str", "version": "int"})
    PolicyPaused = gl.Event("PolicyPaused", {"policy_id": "str"})
    PolicyResumed = gl.Event("PolicyResumed", {"policy_id": "str", "next_due_at": "int"})
    PolicyCancelled = gl.Event("PolicyCancelled", {"policy_id": "str"})
    QueueEntryAdded = gl.Event("QueueEntryAdded", {"policy_id": "str", "next_due_at": "int"})
    QueueEntryRemoved = gl.Event("QueueEntryRemoved", {"policy_id": "str"})
    QueueEntryQuarantined = gl.Event("QueueEntryQuarantined", {"policy_id": "str", "reason": "str"})
    QueuePointerAdvanced = gl.Event("QueuePointerAdvanced", {"new_pointer_index": "int"})
    IntervalCreated = gl.Event("IntervalCreated", {"interval_id": "str", "policy_id": "str"})
    PrecheckFailed = gl.Event("PrecheckFailed", {"policy_id": "str", "reason": "str"})
    DecisionBuy = gl.Event("DecisionBuy", {"policy_id": "str", "interval_id": "str", "selected_asset": "str", "spend_amount": "int"})
    DecisionSkip = gl.Event("DecisionSkip", {"policy_id": "str", "interval_id": "str", "rationale": "str"})
    DecisionReject = gl.Event("DecisionReject", {"policy_id": "str", "interval_id": "str", "reason": "str"})
    ExecutionAuthorized = gl.Event("ExecutionAuthorized", {"instruction_id": "str", "policy_id": "str"})
    SettlementRecorded = gl.Event("SettlementRecorded", {"instruction_id": "str", "tx_hash": "str", "status": "str"})
    PolicyBlocked = gl.Event("PolicyBlocked", {"policy_id": "str", "reason": "str"})
    PolicyRecovered = gl.Event("PolicyRecovered", {"policy_id": "str"})
    EmergencyStopActivated = gl.Event("EmergencyStopActivated", {})
    EmergencyStopCleared = gl.Event("EmergencyStopCleared", {})
    
    def __init__(self):
        self.owner = gl.message.sender_account
        self.config = ProtocolConfig(
            config_version=1,
            pause_mode=False,
            emergency_stop=False,
            supported_assets=["USDC", "ETH"],
            target_asset_allowlist_policy="ALL",
            target_asset_denylist=[],
            approved_venues=["Uniswap", "relay", "jumper exchange"],
            approved_data_sources=["https://api.basescan.org/api"],
            confirmation_threshold=2,
            batch_limit=10,
            retry_policies='{"transient_infrastructure": 3, "transient_market": 3, "transient_user_balance": 5}',
            quote_validity_bounds=300,
            gas_policy='{"max_gas_price": 50000000000}',
            queue_integrity_policy="quarantine"
        )
        self.policies = TreeMap[str, Policy]()
        self.delegations = TreeMap[str, DelegationDescriptor]()
        self.intervals = TreeMap[str, Interval]()
        self.decisions = TreeMap[str, DecisionArtifact]()
        self.instructions = TreeMap[str, ExecutionInstruction]()
        self.attempts = TreeMap[str, ExecutionAttempt]()
        self.settlements = TreeMap[str, SettlementRecord]()
        self.failures = TreeMap[str, FailureRecord]()
        self.queue = DynArray[QueueEntry]()
        self.policy_counter = 0
        self.interval_counter = 0
        self.decision_counter = 0
        self.instruction_counter = 0
        self.attempt_counter = 0
        self.failure_counter = 0

    @gl.public.write
    def update_config(self, new_config: ProtocolConfig) -> None:
        if gl.message.sender_account != self.owner:
            raise gl.UserError("Only owner can update config")
        self.config = new_config

    @gl.public.write
    def toggle_emergency_stop(self, active: bool) -> None:
        if gl.message.sender_account != self.owner:
            raise gl.UserError("Only owner can toggle emergency stop")
        self.config.emergency_stop = active
        if active:
            self.EmergencyStopActivated.emit()
        else:
            self.EmergencyStopCleared.emit()

    @gl.public.write
    def toggle_pause_mode(self, active: bool) -> None:
        if gl.message.sender_account != self.owner:
            raise gl.UserError("Only owner can toggle pause mode")
        self.config.pause_mode = active

    @gl.public.view
    def get_config(self) -> dict:
        return {
            "config_version": self.config.config_version,
            "pause_mode": self.config.pause_mode,
            "emergency_stop": self.config.emergency_stop,
            "supported_assets": self.config.supported_assets,
            "target_asset_allowlist_policy": self.config.target_asset_allowlist_policy,
            "target_asset_denylist": self.config.target_asset_denylist,
            "approved_venues": self.config.approved_venues,
            "confirmation_threshold": self.config.confirmation_threshold,
            "batch_limit": self.config.batch_limit
        }

    @gl.public.write
    def register_policy(
        self,
        owner_wallet: str,
        delegated_executor_wallet: str,
        funding_asset: str,
        target_asset_constraints: str,
        cadence_definition: int,
        nominal_spend_amount: int,
        interval_spend_cap: int,
        rolling_spend_cap: int,
        execution_window_rule: int,
        slippage_rule: int,
        approved_venue_constraints: list[str],
        ai_strategy_profile: str,
        delegation_descriptor_id: str,
        current_time: int
    ) -> str:
        if self.config.pause_mode or self.config.emergency_stop:
            raise gl.UserError("Protocol is paused or under emergency stop")
        self.policy_counter += 1
        policy_id = f"POL-{self.policy_counter}"
        if funding_asset not in self.config.supported_assets:
            raise gl.UserError("Unsupported funding asset")
        policy = Policy(
            policy_id=policy_id,
            owner_wallet=owner_wallet,
            delegated_executor_wallet=delegated_executor_wallet,
            policy_version=1,
            status="Active",
            funding_asset=funding_asset,
            target_asset_constraints=target_asset_constraints,
            cadence_definition=cadence_definition,
            nominal_spend_amount=nominal_spend_amount,
            interval_spend_cap=interval_spend_cap,
            rolling_spend_cap=rolling_spend_cap,
            execution_window_rule=execution_window_rule,
            slippage_rule=slippage_rule,
            approved_venue_constraints=approved_venue_constraints,
            ai_strategy_profile=ai_strategy_profile,
            created_at=current_time,
            updated_at=current_time,
            last_evaluated_at=0,
            last_success_at=0,
            next_due_at=current_time + cadence_definition,
            delegation_descriptor_id=delegation_descriptor_id,
            block_reason="",
            reject_reason=""
        )
        self.policies[policy_id] = policy
        self._add_to_queue(policy_id, policy.next_due_at)
        self.PolicyRegistered.emit(policy_id=policy_id, owner_wallet=owner_wallet)
        return policy_id

    @gl.public.write
    def update_policy(self, policy_id: str, updated_policy: Policy, current_time: int) -> None:
        if not self.policies.has(policy_id):
            raise gl.UserError("Policy not found")
        existing = self.policies[policy_id]
        if existing.status in ["Cancelled"]:
            raise gl.UserError("Cannot update cancelled policy")
        material_change = (
            existing.cadence_definition != updated_policy.cadence_definition or
            existing.nominal_spend_amount != updated_policy.nominal_spend_amount or
            existing.funding_asset != updated_policy.funding_asset or
            existing.target_asset_constraints != updated_policy.target_asset_constraints or
            existing.delegated_executor_wallet != updated_policy.delegated_executor_wallet
        )
        new_version = existing.policy_version
        if material_change:
            new_version += 1
        if existing.status == "Active":
            self._remove_from_queue(policy_id)
            new_next_due = current_time + updated_policy.cadence_definition
            self._add_to_queue(policy_id, new_next_due)
            updated_policy.next_due_at = new_next_due
        updated_policy.policy_id = policy_id
        updated_policy.policy_version = new_version
        updated_policy.updated_at = current_time
        self.policies[policy_id] = updated_policy
        self.PolicyUpdated.emit(policy_id=policy_id, version=new_version)

    @gl.public.write
    def pause_policy(self, policy_id: str) -> None:
        if not self.policies.has(policy_id):
            raise gl.UserError("Policy not found")
        policy = self.policies[policy_id]
        if policy.status != "Active":
            raise gl.UserError("Policy is not Active")
        policy.status = "Paused"
        self.policies[policy_id] = policy
        self._remove_from_queue(policy_id)
        self.PolicyPaused.emit(policy_id=policy_id)

    @gl.public.write
    def resume_policy(self, policy_id: str, current_time: int) -> None:
        if not self.policies.has(policy_id):
            raise gl.UserError("Policy not found")
        policy = self.policies[policy_id]
        if policy.status != "Paused":
            raise gl.UserError("Policy is not Paused")
        policy.status = "Active"
        policy.next_due_at = current_time + policy.cadence_definition
        self.policies[policy_id] = policy
        self._add_to_queue(policy_id, policy.next_due_at)
        self.PolicyResumed.emit(policy_id=policy_id, next_due_at=policy.next_due_at)

    @gl.public.write
    def cancel_policy(self, policy_id: str) -> None:
        if not self.policies.has(policy_id):
            raise gl.UserError("Policy not found")
        policy = self.policies[policy_id]
        policy.status = "Cancelled"
        self.policies[policy_id] = policy
        self._remove_from_queue(policy_id)
        self.PolicyCancelled.emit(policy_id=policy_id)

    @gl.public.write
    def refresh_delegation(self, descriptor_id: str, desc: DelegationDescriptor, current_time: int) -> None:
        self.delegations[descriptor_id] = desc

    def _add_to_queue(self, policy_id: str, next_due_at: int) -> None:
        entry_id = f"Q-{policy_id}"
        new_entry = QueueEntry(
            queue_entry_id=entry_id,
            policy_id=policy_id,
            active_membership=True,
            next_due_at=next_due_at,
            retry_due_at=-1,
            tie_break_key=policy_id,
            traversal_metadata="",
            quarantine_flag=False,
            quarantine_reason="",
            last_pointer_visit_at=0
        )
        inserted = False
        for idx in range(len(self.queue)):
            existing = self.queue[idx]
            if next_due_at < existing.next_due_at:
                self.queue.insert(idx, new_entry)
                inserted = True
                break
            elif next_due_at == existing.next_due_at:
                if policy_id < existing.policy_id:
                    self.queue.insert(idx, new_entry)
                    inserted = True
                    break
        if not inserted:
            self.queue.append(new_entry)
        self.QueueEntryAdded.emit(policy_id=policy_id, next_due_at=next_due_at)

    def _remove_from_queue(self, policy_id: str) -> None:
        found_idx = -1
        for idx in range(len(self.queue)):
            if self.queue[idx].policy_id == policy_id:
                found_idx = idx
                break
        if found_idx != -1:
            self.queue.pop(found_idx)
            self.QueueEntryRemoved.emit(policy_id=policy_id)

    @gl.public.view
    def get_due_batch(self, current_time: int) -> list[str]:
        due_policies = []
        count = 0
        for idx in range(len(self.queue)):
            entry = self.queue[idx]
            if entry.quarantine_flag:
                continue
            effective_due = entry.retry_due_at if entry.retry_due_at != -1 else entry.next_due_at
            if effective_due <= current_time:
                due_policies.append(entry.policy_id)
                count += 1
                if count >= self.config.batch_limit:
                    break
            else:
                break
        return due_policies

    @gl.public.write
    def quarantine_entry(self, policy_id: str, reason: str) -> None:
        for idx in range(len(self.queue)):
            if self.queue[idx].policy_id == policy_id:
                self.queue[idx].quarantine_flag = True
                self.queue[idx].quarantine_reason = reason
                self.QueueEntryQuarantined.emit(policy_id=policy_id, reason=reason)
                break

    @gl.public.write
    def execute_dca_step(self, policy_id: str, current_time: int) -> str:
        if self.config.emergency_stop:
            self.PrecheckFailed.emit(policy_id=policy_id, reason="Emergency Stop active")
            return "ERROR: Emergency Stop"
        if self.config.pause_mode:
            self.PrecheckFailed.emit(policy_id=policy_id, reason="Evaluations paused")
            return "ERROR: Evaluations paused"
        if not self.policies.has(policy_id):
            self.PrecheckFailed.emit(policy_id=policy_id, reason="Policy not found")
            return "ERROR: Policy not found"
        policy = self.policies[policy_id]
        if policy.status != "Active":
            self.PrecheckFailed.emit(policy_id=policy_id, reason="Policy status not Active")
            return f"ERROR: Policy status is {policy.status}"
        self.interval_counter += 1
        interval_id = f"INT-{policy_id}-{self.interval_counter}"
        interval = Interval(
            interval_id=interval_id,
            policy_id=policy_id,
            policy_version=policy.policy_version,
            scheduled_due_at=policy.next_due_at,
            evaluation_state="ReasoningInProgress",
            execution_state="ExecutionPending",
            attempt_count=1,
            last_failure_class="",
            retry_state="",
            terminal_outcome="",
            opened_at=current_time,
            closed_at=0
        )
        self.intervals[interval_id] = interval
        self.IntervalCreated.emit(interval_id=interval_id, policy_id=policy_id)
        allowed_assets = self.config.supported_assets
        denylist = self.config.target_asset_denylist
        strategy_profile = policy.ai_strategy_profile
        nominal_spend = policy.nominal_spend_amount
        funding_asset = policy.funding_asset
        basescan_url = self.config.approved_data_sources[0]
        target_constraints = policy.target_asset_constraints
        def reasoning_nondet():
            prompt = f"""
            You are the DCA Intelligent Agent for GenLayer.
            Evaluate if we should purchase the target asset constraints: {target_constraints}
            using funding asset: {funding_asset} and nominal spend limit of {nominal_spend} units.
            We are checking Basescan API data source: {basescan_url}
            AI Strategy Profile to enforce: {strategy_profile}
            Allowed Assets: {allowed_assets}
            Denylisted Assets: {denylist}
            Evaluate the target token on the following factors:
            - Liquidity: Is there sufficient Uniswap V3 liquidity?
            - Volatility: Are there extreme swings in the last 24h?
            - Momentum: What is the short term price trend?
            - Market Cap: Is it a micro-cap with high risk?
            - Token Age: How long has the contract been deployed?
            - Holder Concentration: Do top holders own >50% of supply?
            - Contract Verification: Is the source code verified on Basescan?
            - Scam Indicators: Are there honeypot or high tax markers?
            - Sentiment: What is the prevailing social sentiment?
            - Confidence Score: (0-100) How confident are you in this decision?
            You must select ONE target asset symbol to purchase if BUY.
            Based on the analysis, output one of three verdicts:
            - BUY: Approve purchase. Choose specific approved target asset and approved spend amount (must be <= {nominal_spend}).
            - SKIP: Do not purchase now, but keep policy active.
            - REJECT: Safety threat detected. Block autonomous execution until user remediation.
            Your output must be strictly valid JSON conforming to this schema:
            {{
                "verdict": "BUY" | "SKIP" | "REJECT",
                "selected_asset": "string or empty",
                "approved_spend_amount": integer,
                "rationale_summary": "concise rationale text",
                "factor_summary": "detailed analysis details",
                "confidence_score": integer,
                "safety_flags": ["string"],
                "evidence": ["string"]
            }}
            """
            response = gl.nondet.exec_prompt(prompt, response_format="json")
            return response
        decision_raw = gl.eq_principle.strict_eq(reasoning_nondet)
        verdict = decision_raw.get("verdict", "SKIP")
        selected_asset = decision_raw.get("selected_asset", "")
        approved_spend = int(decision_raw.get("approved_spend_amount", 0))
        rationale = decision_raw.get("rationale_summary", "Auto evaluation")
        factor_sum = json.dumps(decision_raw.get("factor_summary", {}))
        evidence = decision_raw.get("evidence", [])
        confidence = int(decision_raw.get("confidence_score", 0))
        flags = decision_raw.get("safety_flags", [])
        self.decision_counter += 1
        decision_id = f"DEC-{interval_id}-{self.decision_counter}"
        decision = DecisionArtifact(
            decision_id=decision_id,
            policy_id=policy_id,
            policy_version=policy.policy_version,
            interval_id=interval_id,
            verdict=verdict,
            selected_asset=selected_asset,
            approved_spend_amount=approved_spend,
            rationale_summary=rationale,
            factor_summary=factor_sum,
            evidence_reference_set=evidence,
            confidence_score=confidence,
            safety_flags=flags,
            decision_hash=f"hash-{decision_id}",
            consensus_completed_at=current_time
        )
        self.decisions[decision_id] = decision
        if verdict == "BUY":
            is_valid = True
            err_reason = ""
            if selected_asset in self.config.target_asset_denylist:
                is_valid = False
                err_reason = f"Target asset {selected_asset} is denylisted"
            elif self.config.target_asset_allowlist_policy != "ALL" and selected_asset not in self.config.supported_assets:
                is_valid = False
                err_reason = f"Target asset {selected_asset} is not allowed"
            if approved_spend > policy.nominal_spend_amount:
                is_valid = False
                err_reason = f"Approved spend {approved_spend} exceeds policy limit {policy.nominal_spend_amount}"
            if is_valid:
                self.instruction_counter += 1
                instruction_id = f"INST-{interval_id}-{self.instruction_counter}"
                instruction = ExecutionInstruction(
                    instruction_id=instruction_id,
                    decision_id=decision_id,
                    policy_id=policy_id,
                    interval_id=interval_id,
                    funding_asset=policy.funding_asset,
                    spend_amount=approved_spend,
                    target_asset=selected_asset,
                    approved_venues=policy.approved_venue_constraints,
                    slippage_bound=policy.slippage_rule,
                    instruction_expiry=current_time + self.config.quote_validity_bounds,
                    idempotency_key=instruction_id,
                    validation_snapshot_reference=decision_id
                )
                self.instructions[instruction_id] = instruction
                interval.evaluation_state = "ReasonedBuy"
                interval.execution_state = "ExecutionAuthorized"
                self.intervals[interval_id] = interval
                self.DecisionBuy.emit(policy_id=policy_id, interval_id=interval_id, selected_asset=selected_asset, spend_amount=approved_spend)
                self.ExecutionAuthorized.emit(instruction_id=instruction_id, policy_id=policy_id)
                return f"AUTHORIZED: {instruction_id}"
            else:
                interval.evaluation_state = "PrecheckFailed"
                interval.execution_state = "FailedTerminal"
                interval.terminal_outcome = "failure"
                interval.closed_at=current_time
                self.intervals[interval_id] = interval
                self._remove_from_queue(policy_id)
                policy.next_due_at = current_time + policy.cadence_definition
                self.policies[policy_id] = policy
                self._add_to_queue(policy_id, policy.next_due_at)
                return f"ERROR: Post-check validation failed: {err_reason}"
        elif verdict == "SKIP":
            interval.evaluation_state = "ReasonedSkip"
            interval.execution_state = "Closed"
            interval.terminal_outcome = "skip"
            interval.closed_at=current_time
            self.intervals[interval_id] = interval
            self._remove_from_queue(policy_id)
            policy.next_due_at = current_time + policy.cadence_definition
            self.policies[policy_id] = policy
            self._add_to_queue(policy_id, policy.next_due_at)
            self.DecisionSkip.emit(policy_id=policy_id, interval_id=interval_id, rationale=rationale)
            return "SKIPPED"
        else:
            interval.evaluation_state = "ReasonedReject"
            interval.execution_state = "Closed"
            interval.terminal_outcome = "reject"
            interval.closed_at=current_time
            self.intervals[interval_id] = interval
            policy.status = "Rejected"
            policy.reject_reason = rationale
            self.policies[policy_id] = policy
            self._remove_from_queue(policy_id)
            self.DecisionReject.emit(policy_id=policy_id, interval_id=interval_id, reason=rationale)
            self.PolicyBlocked.emit(policy_id=policy_id, reason=rationale)
            return "REJECTED"

    @gl.public.write
    def record_settlement(
        self,
        instruction_id: str,
        transaction_hash: str,
        venue: str,
        quoted_input_amount: int,
        quoted_min_output: int,
        actual_output_amount: int,
        gas_used: int,
        inclusion_block: int,
        confirmation_block: int,
        current_time: int
    ) -> None:
        if not self.instructions.has(instruction_id):
            raise gl.UserError("Instruction not found")
        instruction = self.instructions[instruction_id]
        interval_id = instruction.interval_id
        interval = self.intervals[interval_id]
        settlement = SettlementRecord(
            instruction_id=instruction_id,
            transaction_hash=transaction_hash,
            venue=venue,
            quoted_input_amount=quoted_input_amount,
            quoted_min_output=quoted_min_output,
            actual_output_amount=actual_output_amount,
            gas_used=gas_used,
            inclusion_block=inclusion_block,
            confirmation_block=confirmation_block,
            settled_at=current_time,
            settlement_status="success"
        )
        self.settlements[instruction_id] = settlement
        interval.execution_state = "ConfirmedSuccess"
        interval.terminal_outcome = "success"
        interval.closed_at = current_time
        self.intervals[interval_id] = interval
        policy_id = instruction.policy_id
        policy = self.policies[policy_id]
        policy.last_success_at = current_time
        policy.last_evaluated_at = current_time
        self._remove_from_queue(policy_id)
        policy.next_due_at = current_time + policy.cadence_definition
        self.policies[policy_id] = policy
        self._add_to_queue(policy_id, policy.next_due_at)
        self.SettlementRecorded.emit(instruction_id=instruction_id, tx_hash=transaction_hash, status="success")

    @gl.public.write
    def record_failure(
        self,
        instruction_id: str,
        failure_class: str,
        cause: str,
        detected_by: str,
        retriable: bool,
        current_time: int
    ) -> None:
        if not self.instructions.has(instruction_id):
            raise gl.UserError("Instruction not found")
        instruction = self.instructions[instruction_id]
        interval_id = instruction.interval_id
        interval = self.intervals[interval_id]
        self.failure_counter += 1
        failure_id = f"FAIL-{self.failure_counter}"
        failure = FailureRecord(
            failure_id=failure_id,
            policy_id=instruction.policy_id,
            interval_id=interval_id,
            instruction_id=instruction_id,
            layer="BaseMainnet",
            failure_class=failure_class,
            cause=cause,
            detected_by=detected_by,
            retriable=retriable,
            retry_policy_reference="",
            recovery_requirement="",
            scope_of_impact="Interval"
        )
        self.failures[instruction_id] = failure
        policy_id = instruction.policy_id
        policy = self.policies[policy_id]
        if retriable and interval.attempt_count < 3:
            interval.attempt_count += 1
            interval.execution_state = "FailedRetriable"
            self.intervals[interval_id] = interval
            for idx in range(len(self.queue)):
                if self.queue[idx].policy_id == policy_id:
                    self.queue[idx].retry_due_at = current_time + 300
                    break
        else:
            interval.execution_state = "FailedTerminal"
            interval.terminal_outcome = "failure"
            interval.closed_at = current_time
            self.intervals[interval_id] = interval
            policy.status = "Blocked"
            policy.block_reason = cause
            self.policies[policy_id] = policy
            self._remove_from_queue(policy_id)
            self.PolicyBlocked.emit(policy_id=policy_id, reason=cause)
        self.SettlementRecorded.emit(instruction_id=instruction_id, tx_hash="", status="failed")

    # ==================== VIEW METHODS ====================

    @gl.public.view
    def get_policy(self, policy_id: str) -> str:
        if not self.policies.has(policy_id):
            return "{}"
        p = self.policies[policy_id]
        return json.dumps({
            "policy_id": p.policy_id,
            "owner_wallet": p.owner_wallet,
            "delegated_executor_wallet": p.delegated_executor_wallet,
            "policy_version": p.policy_version,
            "status": p.status,
            "funding_asset": p.funding_asset,
            "target_asset_constraints": p.target_asset_constraints,
            "cadence_definition": p.cadence_definition,
            "nominal_spend_amount": p.nominal_spend_amount,
            "interval_spend_cap": p.interval_spend_cap,
            "rolling_spend_cap": p.rolling_spend_cap,
            "next_due_at": p.next_due_at,
            "block_reason": p.block_reason,
            "reject_reason": p.reject_reason
        })

    @gl.public.view
    def get_queue(self) -> str:
        res = []
        for idx in range(len(self.queue)):
            entry = self.queue[idx]
            res.append({
                "policy_id": entry.policy_id,
                "next_due_at": entry.next_due_at,
                "retry_due_at": entry.retry_due_at,
                "quarantine_flag": entry.quarantine_flag,
                "quarantine_reason": entry.quarantine_reason
            })
        return json.dumps(res)

    @gl.public.view
    def get_interval(self, interval_id: str) -> str:
        if not self.intervals.has(interval_id):
            return "{}"
        i = self.intervals[interval_id]
        return json.dumps({
            "interval_id": i.interval_id,
            "policy_id": i.policy_id,
            "evaluation_state": i.evaluation_state,
            "execution_state": i.execution_state,
            "attempt_count": i.attempt_count,
            "terminal_outcome": i.terminal_outcome
        })

    @gl.public.view
    def get_decision(self, decision_id: str) -> str:
        if not self.decisions.has(decision_id):
            return "{}"
        d = self.decisions[decision_id]
        return json.dumps({
            "decision_id": d.decision_id,
            "policy_id": d.policy_id,
            "verdict": d.verdict,
            "selected_asset": d.selected_asset,
            "approved_spend_amount": d.approved_spend_amount,
            "rationale_summary": d.rationale_summary,
            "confidence_score": d.confidence_score
        })

    @gl.public.view
    def get_instruction(self, instruction_id: str) -> str:
        if not self.instructions.has(instruction_id):
            return "{}"
        i = self.instructions[instruction_id]
        return json.dumps({
            "instruction_id": i.instruction_id,
            "decision_id": i.decision_id,
            "policy_id": i.policy_id,
            "interval_id": i.interval_id,
            "funding_asset": i.funding_asset,
            "spend_amount": i.spend_amount,
            "target_asset": i.target_asset,
            "approved_venues": i.approved_venues,
            "slippage_bound": i.slippage_bound,
            "instruction_expiry": i.instruction_expiry
        })
