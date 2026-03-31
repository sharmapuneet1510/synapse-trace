import type { TraceResult } from '../types/trace';

export const DUMMY_TRACE: TraceResult = {
  trace_id: 'trace-20260330-N_CLEARED-001',
  field_name: 'N_CLEARED',
  origin: 'XSLT_THEN_JAVA',
  summary: {
    field_name: 'N_CLEARED',
    origin: 'XSLT_THEN_JAVA',
    pipeline_steps: [
      'Extract from trade message (XSLT)',
      'Map to internal model',
      'Apply jurisdiction enrichment',
      'Evaluate clearing conditions',
      'Final report assignment',
    ],
    branch_count: 4,
    total_nodes: 9,
    has_xslt: true,
    has_java: true,
    technical_explanation:
      'N_CLEARED originates in mapTradeMessage.xslt via //Trade/Cleared. It is carried forward through TradeEnricher.enrich() and evaluated in ClearingDecisionService.evaluate() with four conditional branches covering CCP, bilateral, and default clearing scenarios. Final value is assigned in ReportBuilder.buildClearingFlag().',
    business_explanation:
      'Indicates whether a trade has been submitted to and confirmed by a central counterparty (CCP). Used for regulatory reporting (EMIR/CFTC) to determine if mandatory clearing applies. A value of "Y" triggers CCP reporting obligations; "N" or null routes to bilateral trade reporting.',
  },
  pipeline: [
    {
      step_id: 'step-xslt-extract',
      order: 0,
      label: 'mapTradeMessage.xslt',
      type: 'xslt_template',
      transformation_type: 'EXTRACTION',
      evidence: {
        repository: 'lib-trade-mapping',
        module: 'xslt-core',
        file_path: 'src/main/resources/xslt/mapTradeMessage.xslt',
        line_number: 142,
        class_or_template: 'mapTradeMessage',
        method_or_template_name: 'extractClearedFlag',
        raw_code: '<xsl:value-of select="//Trade/ClearedIndicator" />',
      },
    },
    {
      step_id: 'step-java-enrich',
      order: 1,
      label: 'TradeEnricher.enrich()',
      type: 'java_method',
      transformation_type: 'ENRICHMENT',
      evidence: {
        repository: 'trade-enrichment-svc',
        module: 'enrichment',
        package: 'com.corp.trade.enrichment',
        file_path: 'src/main/java/com/corp/trade/enrichment/TradeEnricher.java',
        line_number: 88,
        class_or_template: 'TradeEnricher',
        method_or_template_name: 'enrich',
        raw_code: 'trade.setClearedFlag(resolveClearing(trade.getProductType(), trade.getCounterpartyType()));',
      },
    },
    {
      step_id: 'step-java-jurisdiction',
      order: 2,
      label: 'JurisdictionFilter.apply()',
      type: 'java_method',
      transformation_type: 'MAPPING',
      evidence: {
        repository: 'trade-enrichment-svc',
        module: 'jurisdiction',
        package: 'com.corp.trade.jurisdiction',
        file_path: 'src/main/java/com/corp/trade/jurisdiction/JurisdictionFilter.java',
        line_number: 55,
        class_or_template: 'JurisdictionFilter',
        method_or_template_name: 'apply',
        raw_code: 'if (EMIR_JURISDICTIONS.contains(trade.getJurisdiction())) { trade.setMandatoryClearing(true); }',
      },
    },
    {
      step_id: 'step-java-clearing-decision',
      order: 3,
      label: 'ClearingDecisionService.evaluate()',
      type: 'java_method',
      transformation_type: 'CONDITIONAL_ASSIGNMENT',
      evidence: {
        repository: 'clearing-decision-svc',
        module: 'decision',
        package: 'com.corp.clearing',
        file_path: 'src/main/java/com/corp/clearing/ClearingDecisionService.java',
        line_number: 203,
        class_or_template: 'ClearingDecisionService',
        method_or_template_name: 'evaluate',
        condition_text: 'isMandatoryClearing && ccpEligible && notExempt',
        raw_code: 'return (isMandatoryClearing && ccpEligible && !isExempt) ? "Y" : "N";',
      },
    },
    {
      step_id: 'step-java-override',
      order: 4,
      label: 'ClearingOverrideService.check()',
      type: 'java_method',
      transformation_type: 'OVERRIDE',
      evidence: {
        repository: 'clearing-decision-svc',
        module: 'override',
        package: 'com.corp.clearing',
        file_path: 'src/main/java/com/corp/clearing/ClearingOverrideService.java',
        line_number: 78,
        class_or_template: 'ClearingOverrideService',
        method_or_template_name: 'check',
        condition_text: 'manualOverride == true',
        raw_code: 'if (trade.hasManualOverride()) { return trade.getOverrideValue(); }',
      },
    },
    {
      step_id: 'step-java-report',
      order: 5,
      label: 'ReportBuilder.buildClearingFlag()',
      type: 'java_method',
      transformation_type: 'FINAL_REPORT_ASSIGNMENT',
      evidence: {
        repository: 'report-builder-svc',
        module: 'builder',
        package: 'com.corp.report',
        file_path: 'src/main/java/com/corp/report/ReportBuilder.java',
        line_number: 312,
        class_or_template: 'ReportBuilder',
        method_or_template_name: 'buildClearingFlag',
        raw_code: 'report.setNCleared(resolvedValue != null ? resolvedValue : DEFAULT_CLEARED_FLAG);',
      },
    },
  ],
  branches: [
    {
      branch_id: 'branch-ccp-mandatory',
      condition: 'isMandatoryClearing && ccpEligible && !isExempt',
      outcome: '"Y" — CCP cleared, EMIR/CFTC reporting required',
      nodes: ['step-java-clearing-decision', 'step-java-report'],
      edges: [],
    },
    {
      branch_id: 'branch-bilateral',
      condition: 'isMandatoryClearing && !ccpEligible',
      outcome: '"N" — Bilateral, exemption reporting required',
      nodes: ['step-java-clearing-decision', 'step-java-report'],
      edges: [],
    },
    {
      branch_id: 'branch-voluntary',
      condition: '!isMandatoryClearing && voluntaryClearing',
      outcome: '"Y" — Voluntary CCP clearing',
      nodes: ['step-java-jurisdiction', 'step-java-clearing-decision'],
      edges: [],
    },
    {
      branch_id: 'branch-override',
      condition: 'manualOverride == true',
      outcome: 'Override value applied, audit trail written',
      nodes: ['step-java-override', 'step-java-report'],
      edges: [],
    },
  ],
  evidence: [],
  technical_explanation:
    'N_CLEARED originates in mapTradeMessage.xslt via //Trade/Cleared. It is carried forward through TradeEnricher.enrich() and evaluated in ClearingDecisionService.evaluate() with four conditional branches covering CCP, bilateral, and default clearing scenarios.',
  business_explanation:
    'Indicates whether a trade has been submitted to and confirmed by a CCP. Used for regulatory reporting (EMIR/CFTC).',
  graph_json: {
    nodes: [
      { id: 'step-xslt-extract', label: 'mapTradeMessage.xslt', type: 'xslt_template', properties: { transformation_type: 'EXTRACTION' } },
      { id: 'step-java-enrich', label: 'TradeEnricher.enrich()', type: 'java_method', properties: { transformation_type: 'ENRICHMENT' } },
      { id: 'step-java-jurisdiction', label: 'JurisdictionFilter.apply()', type: 'java_method', properties: { transformation_type: 'MAPPING' } },
      { id: 'step-java-clearing-decision', label: 'ClearingDecisionService.evaluate()', type: 'java_method', properties: { transformation_type: 'CONDITIONAL_ASSIGNMENT' } },
      { id: 'step-java-override', label: 'ClearingOverrideService.check()', type: 'java_method', properties: { transformation_type: 'OVERRIDE' } },
      { id: 'step-java-report', label: 'ReportBuilder.buildClearingFlag()', type: 'java_method', properties: { transformation_type: 'FINAL_REPORT_ASSIGNMENT' } },
    ],
    edges: [
      { source: 'step-xslt-extract', target: 'step-java-enrich', relation: 'feeds', properties: {} },
      { source: 'step-java-enrich', target: 'step-java-jurisdiction', relation: 'feeds', properties: {} },
      { source: 'step-java-jurisdiction', target: 'step-java-clearing-decision', relation: 'feeds', properties: {} },
      { source: 'step-java-clearing-decision', target: 'step-java-override', relation: 'conditionally_feeds', properties: {} },
      { source: 'step-java-clearing-decision', target: 'step-java-report', relation: 'feeds', properties: {} },
      { source: 'step-java-override', target: 'step-java-report', relation: 'overrides', properties: {} },
    ],
    metadata: {},
  },
  metadata: {
    scan_duration_ms: 847,
    lib_repos: ['lib-trade-mapping', 'xslt-commons'],
    project_repos: ['trade-enrichment-svc', 'clearing-decision-svc', 'report-builder-svc'],
    deep_scan_packages: ['com.corp.clearing', 'com.corp.trade'],
  },
};

// ── TRADE_STATUS — multi-downstream / multi-end-node example ──────────────────
export const DUMMY_TRADE_STATUS: TraceResult = {
  trace_id: 'trace-20260331-TRADE_STATUS-001',
  field_name: 'TRADE_STATUS',
  origin: 'XSLT_THEN_JAVA',
  summary: {
    field_name: 'TRADE_STATUS',
    origin: 'XSLT_THEN_JAVA',
    pipeline_steps: [
      'Extract lifecycle state from FpML (XSLT)',
      'Validate state-machine transition',
      'Enrich with counterparty eligibility',
      'Evaluate risk engine (fork point)',
      '→ Submit to settlement bridge',
      '→ Build regulatory status report',
      '→ Map to risk ledger entry',
      '→ Write audit trail',
      '→ Confirm with CCP',
    ],
    branch_count: 3,
    total_nodes: 14,
    has_xslt: true,
    has_java: true,
    technical_explanation:
      'TRADE_STATUS originates in mapTradeLifecycle.xslt. After validation and enrichment, RiskEngine.evaluate() fans out to three parallel downstream systems: SettlementBridge (DTCC/LCH), ReportingEngine (MiFIR/EMIR), and RegulatoryMapper (SEC/FCA). ReportingEngine and RegulatoryMapper each have their own terminal nodes — AuditTrail.write() and ConfirmationService.confirm() respectively — yielding five end-nodes total.',
    business_explanation:
      'TRADE_STATUS tracks the full post-trade lifecycle: new → confirmed → cleared → settled. Downstream consumption drives three parallel flows: (1) settlement instructions to CCP/CSD, (2) trade-state reports to regulators under MiFIR Art.26 / EMIR RTS, and (3) risk position updates. Any status change must propagate consistently to all five terminal consumers; failure in any path triggers a reconciliation alert.',
  },

  pipeline: [
    {
      step_id: 'ts-xslt-extract',
      order: 0,
      label: 'mapTradeLifecycle.xslt',
      type: 'xslt_template',
      transformation_type: 'EXTRACTION',
      evidence: {
        repository: 'lib-fpml-mapping',
        module: 'lifecycle',
        file_path: 'src/main/resources/xslt/mapTradeLifecycle.xslt',
        line_number: 87,
        class_or_template: 'mapTradeLifecycle',
        method_or_template_name: 'extractTradeStatus',
        raw_code: '<xsl:value-of select="//fpml:trade/fpml:tradeHeader/fpml:tradeStatus" />',
      },
    },
    {
      step_id: 'ts-validator',
      order: 1,
      label: 'TradeStateValidator.validate()',
      type: 'java_method',
      transformation_type: 'MAPPING',
      evidence: {
        repository: 'trade-lifecycle-svc',
        module: 'validation',
        package: 'com.corp.trade.lifecycle',
        file_path: 'src/main/java/com/corp/trade/lifecycle/TradeStateValidator.java',
        line_number: 44,
        class_or_template: 'TradeStateValidator',
        method_or_template_name: 'validate',
        raw_code: 'StateMachine.assertValidTransition(prev, next);',
      },
    },
    {
      step_id: 'ts-enricher',
      order: 2,
      label: 'StatusEnricher.enrich()',
      type: 'java_method',
      transformation_type: 'ENRICHMENT',
      evidence: {
        repository: 'trade-lifecycle-svc',
        module: 'enrichment',
        package: 'com.corp.trade.lifecycle',
        file_path: 'src/main/java/com/corp/trade/lifecycle/StatusEnricher.java',
        line_number: 112,
        class_or_template: 'StatusEnricher',
        method_or_template_name: 'enrich',
        raw_code: 'trade.setEligibleForClearing(ccpEligibilityService.check(trade));',
      },
    },
    {
      step_id: 'ts-risk-engine',
      order: 3,
      label: 'RiskEngine.evaluate()',
      type: 'java_method',
      transformation_type: 'CONDITIONAL_ASSIGNMENT',
      evidence: {
        repository: 'risk-engine-svc',
        module: 'evaluation',
        package: 'com.corp.risk',
        file_path: 'src/main/java/com/corp/risk/RiskEngine.java',
        line_number: 318,
        class_or_template: 'RiskEngine',
        method_or_template_name: 'evaluate',
        condition_text: 'status IN {CONFIRMED, CLEARED, SETTLED}',
        raw_code: 'dispatcher.fanOut(trade, statusRoutes);',
      },
    },
    // Downstream — settlement path
    {
      step_id: 'ts-settlement-bridge',
      order: 4,
      label: 'SettlementBridge.submit()',
      type: 'java_method',
      transformation_type: 'PASS_THROUGH',
      evidence: {
        repository: 'settlement-adapter-svc',
        module: 'bridge',
        package: 'com.corp.settlement',
        file_path: 'src/main/java/com/corp/settlement/SettlementBridge.java',
        line_number: 67,
        class_or_template: 'SettlementBridge',
        method_or_template_name: 'submit',
        raw_code: 'dtcc.submitInstruction(instruction);',
      },
    },
    // Downstream — reporting path
    {
      step_id: 'ts-report-builder',
      order: 5,
      label: 'ReportingEngine.buildStatus()',
      type: 'java_method',
      transformation_type: 'FINAL_REPORT_ASSIGNMENT',
      evidence: {
        repository: 'report-builder-svc',
        module: 'status',
        package: 'com.corp.report',
        file_path: 'src/main/java/com/corp/report/ReportingEngine.java',
        line_number: 201,
        class_or_template: 'ReportingEngine',
        method_or_template_name: 'buildStatus',
        raw_code: 'report.setTradeStatus(resolvedStatus);',
      },
    },
    // Downstream — regulatory path
    {
      step_id: 'ts-regulatory-mapper',
      order: 6,
      label: 'RegulatoryMapper.map()',
      type: 'java_method',
      transformation_type: 'MAPPING',
      evidence: {
        repository: 'regulatory-filing-svc',
        module: 'mapper',
        package: 'com.corp.regulatory',
        file_path: 'src/main/java/com/corp/regulatory/RegulatoryMapper.java',
        line_number: 89,
        class_or_template: 'RegulatoryMapper',
        method_or_template_name: 'map',
        raw_code: 'return EMIR_STATUS_MAP.get(trade.getStatus());',
      },
    },
    // Terminal — audit
    {
      step_id: 'ts-audit-trail',
      order: 7,
      label: 'AuditTrail.write()',
      type: 'java_method',
      transformation_type: 'FINAL_REPORT_ASSIGNMENT',
      evidence: {
        repository: 'audit-svc',
        module: 'writer',
        package: 'com.corp.audit',
        file_path: 'src/main/java/com/corp/audit/AuditTrail.java',
        line_number: 33,
        class_or_template: 'AuditTrail',
        method_or_template_name: 'write',
        raw_code: 'auditRepo.save(AuditEvent.of(trade, TRADE_STATUS));',
      },
    },
    // Terminal — CCP confirmation
    {
      step_id: 'ts-confirmation-svc',
      order: 8,
      label: 'ConfirmationService.confirm()',
      type: 'java_method',
      transformation_type: 'FINAL_REPORT_ASSIGNMENT',
      evidence: {
        repository: 'regulatory-filing-svc',
        module: 'confirmation',
        package: 'com.corp.regulatory',
        file_path: 'src/main/java/com/corp/regulatory/ConfirmationService.java',
        line_number: 55,
        class_or_template: 'ConfirmationService',
        method_or_template_name: 'confirm',
        raw_code: 'ccp.sendAcknowledgement(trade.getUTI(), resolvedStatus);',
      },
    },
  ],

  branches: [
    {
      branch_id: 'branch-confirmed',
      condition: 'status == CONFIRMED && ccpEligible',
      outcome: 'Routes to settlement bridge + regulatory confirmation',
      nodes: ['ts-risk-engine', 'ts-settlement-bridge', 'ts-confirmation-svc'],
      edges: [],
    },
    {
      branch_id: 'branch-cleared',
      condition: 'status == CLEARED && !settlementPending',
      outcome: 'Builds regulatory report; writes audit entry',
      nodes: ['ts-risk-engine', 'ts-report-builder', 'ts-audit-trail'],
      edges: [],
    },
    {
      branch_id: 'branch-terminated',
      condition: 'status IN {CANCELLED, MATURED, NOVATED}',
      outcome: 'Regulatory mapping only; settlement skipped',
      nodes: ['ts-risk-engine', 'ts-regulatory-mapper', 'ts-audit-trail'],
      edges: [],
    },
  ],

  evidence: [],
  technical_explanation:
    'TRADE_STATUS fans out from RiskEngine.evaluate() to three parallel downstream subsystems.',
  business_explanation:
    'Post-trade status drives settlement, regulatory reporting, and risk position simultaneously.',

  graph_json: {
    nodes: [
      { id: 'ts-xslt-extract',      label: 'mapTradeLifecycle.xslt',        type: 'xslt_template', properties: { transformation_type: 'EXTRACTION' } },
      { id: 'ts-validator',          label: 'TradeStateValidator.validate()', type: 'java_method',   properties: { transformation_type: 'MAPPING' } },
      { id: 'ts-enricher',           label: 'StatusEnricher.enrich()',        type: 'java_method',   properties: { transformation_type: 'ENRICHMENT' } },
      { id: 'ts-risk-engine',        label: 'RiskEngine.evaluate()',          type: 'java_method',   properties: { transformation_type: 'CONDITIONAL_ASSIGNMENT' } },
      { id: 'ts-settlement-bridge',  label: 'SettlementBridge.submit()',      type: 'java_method',   properties: { transformation_type: 'PASS_THROUGH' } },
      { id: 'ts-report-builder',     label: 'ReportingEngine.buildStatus()',  type: 'java_method',   properties: { transformation_type: 'FINAL_REPORT_ASSIGNMENT' } },
      { id: 'ts-regulatory-mapper',  label: 'RegulatoryMapper.map()',         type: 'java_method',   properties: { transformation_type: 'MAPPING' } },
      { id: 'ts-audit-trail',        label: 'AuditTrail.write()',             type: 'java_method',   properties: { transformation_type: 'FINAL_REPORT_ASSIGNMENT' } },
      { id: 'ts-confirmation-svc',   label: 'ConfirmationService.confirm()',  type: 'java_method',   properties: { transformation_type: 'FINAL_REPORT_ASSIGNMENT' } },
    ],
    edges: [
      { source: 'ts-xslt-extract',     target: 'ts-validator',         relation: 'feeds',              properties: {} },
      { source: 'ts-validator',         target: 'ts-enricher',          relation: 'feeds',              properties: {} },
      { source: 'ts-enricher',          target: 'ts-risk-engine',       relation: 'feeds',              properties: {} },
      // Fan-out from risk engine → 3 parallel paths
      { source: 'ts-risk-engine',       target: 'ts-settlement-bridge', relation: 'routes_to',          properties: {} },
      { source: 'ts-risk-engine',       target: 'ts-report-builder',    relation: 'routes_to',          properties: {} },
      { source: 'ts-risk-engine',       target: 'ts-regulatory-mapper', relation: 'routes_to',          properties: {} },
      // report-builder → audit
      { source: 'ts-report-builder',    target: 'ts-audit-trail',       relation: 'triggers',           properties: {} },
      // regulatory-mapper → confirmation
      { source: 'ts-regulatory-mapper', target: 'ts-confirmation-svc',  relation: 'triggers',           properties: {} },
    ],
    metadata: { is_dag: true, fan_out_node: 'ts-risk-engine', end_nodes: ['ts-settlement-bridge', 'ts-audit-trail', 'ts-confirmation-svc'] },
  },

  metadata: {
    scan_duration_ms: 1124,
    lib_repos: ['lib-fpml-mapping'],
    project_repos: ['trade-lifecycle-svc', 'risk-engine-svc', 'settlement-adapter-svc', 'report-builder-svc', 'regulatory-filing-svc', 'audit-svc'],
    deep_scan_packages: ['com.corp.trade.lifecycle', 'com.corp.risk', 'com.corp.settlement', 'com.corp.report', 'com.corp.regulatory'],
  },
};

export const FIELD_DUMMY_MAP: Record<string, TraceResult> = {
  N_CLEARED: null as unknown as TraceResult,   // filled below
  TRADE_STATUS: DUMMY_TRADE_STATUS,
};

export const DUMMY_LOGS = [
  { id: '1', timestamp: '2026-03-30T09:14:01.123Z', level: 'INFO', module: 'scanner', message: 'Starting scan for field N_CLEARED', trace_id: 'trace-20260330-N_CLEARED-001' },
  { id: '2', timestamp: '2026-03-30T09:14:01.245Z', level: 'INFO', module: 'xslt-parser', message: 'Loaded 12 XSLT templates from lib-trade-mapping', trace_id: 'trace-20260330-N_CLEARED-001' },
  { id: '3', timestamp: '2026-03-30T09:14:01.389Z', level: 'DEBUG', module: 'xslt-parser', message: 'Found origin: mapTradeMessage.xslt:142 → extractClearedFlag', trace_id: 'trace-20260330-N_CLEARED-001' },
  { id: '4', timestamp: '2026-03-30T09:14:01.502Z', level: 'INFO', module: 'java-parser', message: 'Scanning 3 packages in trade-enrichment-svc', trace_id: 'trace-20260330-N_CLEARED-001' },
  { id: '5', timestamp: '2026-03-30T09:14:01.710Z', level: 'INFO', module: 'java-parser', message: 'Resolved TradeEnricher.enrich() → line 88', trace_id: 'trace-20260330-N_CLEARED-001' },
  { id: '6', timestamp: '2026-03-30T09:14:01.823Z', level: 'INFO', module: 'condition-tracer', message: 'Extracted 4 branch conditions from ClearingDecisionService', trace_id: 'trace-20260330-N_CLEARED-001' },
  { id: '7', timestamp: '2026-03-30T09:14:01.901Z', level: 'WARN', module: 'condition-tracer', message: 'Potential override path detected in ClearingOverrideService.check()', trace_id: 'trace-20260330-N_CLEARED-001' },
  { id: '8', timestamp: '2026-03-30T09:14:01.970Z', level: 'INFO', module: 'stitcher', message: 'Pipeline assembled: 6 nodes, 6 edges', trace_id: 'trace-20260330-N_CLEARED-001' },
  { id: '9', timestamp: '2026-03-30T09:14:01.987Z', level: 'INFO', module: 'scanner', message: 'Scan complete in 847ms — 9 total nodes, 4 branches', trace_id: 'trace-20260330-N_CLEARED-001' },
];

export const DUMMY_CHAT_SESSIONS = [
  { id: 'sess-001', title: 'N_CLEARED clearing logic', created_at: '2026-03-30T08:00:00Z', updated_at: '2026-03-30T09:05:00Z', message_count: 4 },
  { id: 'sess-002', title: 'EMIR reporting scope', created_at: '2026-03-29T14:22:00Z', updated_at: '2026-03-29T14:35:00Z', message_count: 6 },
  { id: 'sess-003', title: 'Override audit trail', created_at: '2026-03-28T11:00:00Z', updated_at: '2026-03-28T11:18:00Z', message_count: 2 },
];

export const DUMMY_CHAT_MESSAGES = [
  {
    id: 'msg-001', session_id: 'sess-001', role: 'user' as const,
    content: 'What triggers the N_CLEARED field to be set to "Y"?',
    field_name: 'N_CLEARED', created_at: '2026-03-30T08:01:00Z',
  },
  {
    id: 'msg-002', session_id: 'sess-001', role: 'assistant' as const,
    content: 'N_CLEARED is set to "Y" when three conditions are simultaneously true:\n\n1. **isMandatoryClearing** — the jurisdiction (e.g. EU under EMIR, US under CFTC) mandates central clearing for this product class\n2. **ccpEligible** — the instrument is eligible for clearing at the designated CCP\n3. **!isExempt** — no clearing exemption applies (e.g. intra-group, pension fund temporary exemption)\n\nThis logic lives in `ClearingDecisionService.evaluate()` at line 203.',
    field_name: 'N_CLEARED', created_at: '2026-03-30T08:01:45Z',
  },
  {
    id: 'msg-003', session_id: 'sess-001', role: 'user' as const,
    content: 'What happens if there is a manual override?',
    field_name: 'N_CLEARED', created_at: '2026-03-30T08:03:00Z',
  },
  {
    id: 'msg-004', session_id: 'sess-001', role: 'assistant' as const,
    content: 'Manual overrides are handled by `ClearingOverrideService.check()` (line 78). When `trade.hasManualOverride()` returns true, the override value bypasses the standard decision logic and flows directly to `ReportBuilder.buildClearingFlag()`. An audit trail entry is written to the override log table. This path is represented as the "branch-override" branch in the lineage graph.',
    field_name: 'N_CLEARED', created_at: '2026-03-30T08:03:55Z',
  },
];

export const DUMMY_RECENT_TRACES = ['N_CLEARED', 'TRADE_STATUS', 'REPORTING_FLAG', 'COUNTERPARTY_ID'];

// Populate after DUMMY_TRACE is defined
FIELD_DUMMY_MAP['N_CLEARED'] = DUMMY_TRACE;
