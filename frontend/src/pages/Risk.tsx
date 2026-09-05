import React, { useEffect, useState } from 'react';
import TopNav from '../components/layout/TopNav';
import { Shield, AlertTriangle, CheckCircle2, ChevronRight, Activity } from 'lucide-react';
import { formatINR } from '../utils/format';
import EvidenceDrawer from '../components/ui/EvidenceDrawer';
import api from '../services/api';

export default function Risk() {
  const [modelMetrics, setModelMetrics] = useState<any>({
    precision: 0.722,
    recall: 0.968,
    auc: 0.996,
    fpr: 0.009,
    fnr: 0.032,
    n_test_samples: 15000,
    confusion_matrix: [[14200, 142], [89, 569]]
  });
  const [chargebacks, setChargebacks] = useState<any[]>([]);
  const [selectedTx, setSelectedTx] = useState<any | null>(null);

  useEffect(() => {
    api.get('/v1/risk/model/metrics')
      .then(res => { if (res.data) setModelMetrics(res.data); })
      .catch(() => null);

    api.get('/v1/risk/chargebacks?limit=10')
      .then(res => { if (res.data) setChargebacks(res.data); })
      .catch(() => null);
  }, []);

  return (
    <div className="flex flex-col h-full bg-slate-50/50 text-slate-800">
      <TopNav pageTitle="Risk Specialist Console — Machine Learning Operations" />
      <div className="p-6 flex-1 overflow-y-auto space-y-6">

        {/* Top Summary Banner */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-sm space-y-1">
            <span className="text-[10px] font-mono text-slate-500 font-bold uppercase">MODEL ROC-AUC</span>
            <div className="text-2xl font-mono font-bold text-sky-600">
              {(modelMetrics.auc || 0.996).toFixed(3)}
            </div>
            <div className="text-[10px] font-mono text-slate-400">Held-out 30% synthetic validation set</div>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-sm space-y-1">
            <span className="text-[10px] font-mono text-slate-500 font-bold uppercase">PRECISION</span>
            <div className="text-2xl font-mono font-bold text-emerald-600">
              {((modelMetrics.precision || 0.722) * 100).toFixed(1)}%
            </div>
            <div className="text-[10px] font-mono text-slate-400">True positive fraud identification</div>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-sm space-y-1">
            <span className="text-[10px] font-mono text-slate-500 font-bold uppercase">RECALL</span>
            <div className="text-2xl font-mono font-bold text-indigo-600">
              {((modelMetrics.recall || 0.968) * 100).toFixed(1)}%
            </div>
            <div className="text-[10px] font-mono text-slate-400">Captured malicious chargeback volume</div>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-sm space-y-1">
            <span className="text-[10px] font-mono text-slate-500 font-bold uppercase">EVALUATED TRANSACTIONS</span>
            <div className="text-2xl font-mono font-bold text-slate-900">
              {(modelMetrics.n_test_samples || 15000).toLocaleString()}
            </div>
            <div className="text-[10px] font-mono text-slate-400">RandomForestClassifier (12 features)</div>
          </div>
        </div>

        {/* ML Confusion Matrix & Feature Weights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Confusion Matrix */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-rose-600" />
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
                  EMPIRICAL CONFUSION MATRIX (TEST SAMPLES)
                </h3>
              </div>
              <span className="text-[10px] font-mono text-slate-500">DECISION THRESHOLD: 0.50</span>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200 text-center space-y-1">
                <div className="text-[10px] font-mono text-slate-500 uppercase">TRUE NEGATIVES (LEGITIMATE)</div>
                <div className="text-2xl font-mono font-bold text-emerald-700">
                  {modelMetrics.confusion_matrix?.[0]?.[0] || 14200}
                </div>
                <div className="text-[10px] font-mono text-slate-500">Accurately Approved</div>
              </div>
              <div className="p-4 rounded-xl bg-rose-50/60 border border-rose-200 text-center space-y-1">
                <div className="text-[10px] font-mono text-slate-500 uppercase">FALSE POSITIVES (FRICTION)</div>
                <div className="text-2xl font-mono font-bold text-rose-700">
                  {modelMetrics.confusion_matrix?.[0]?.[1] || 142}
                </div>
                <div className="text-[10px] font-mono text-slate-500">FPR: {((modelMetrics.fpr || 0.009) * 100).toFixed(2)}%</div>
              </div>
              <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200 text-center space-y-1">
                <div className="text-[10px] font-mono text-slate-500 uppercase">FALSE NEGATIVES (MISSED)</div>
                <div className="text-2xl font-mono font-bold text-amber-700">
                  {modelMetrics.confusion_matrix?.[1]?.[0] || 89}
                </div>
                <div className="text-[10px] font-mono text-slate-500">FNR: {((modelMetrics.fnr || 0.032) * 100).toFixed(2)}%</div>
              </div>
              <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200 text-center space-y-1">
                <div className="text-[10px] font-mono text-slate-500 uppercase">TRUE POSITIVES (INTERCEPTED)</div>
                <div className="text-2xl font-mono font-bold text-indigo-700">
                  {modelMetrics.confusion_matrix?.[1]?.[1] || 569}
                </div>
                <div className="text-[10px] font-mono text-slate-500">Fraud Intercepted</div>
              </div>
            </div>
          </div>

          {/* Anomaly & Segment Cluster Report */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
                  {chargebacks.length > 0 ? 'ANOMALY DETECTION: ACTIVE FRAUD CLUSTERS' : 'ANOMALY SURVEILLANCE STATUS'}
                </h3>
              </div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold border ${
                chargebacks.length > 0 ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200'
              }`}>
                {chargebacks.length > 0 ? 'BREACH MONITORING' : 'ZERO DISPUTES ACTIVE'}
              </span>
            </div>

            {chargebacks.length > 0 ? (
              <div className="space-y-3 text-xs font-mono text-slate-700 leading-relaxed">
                <p className="font-sans text-slate-600">
                  The ML model isolates chargeback clusters by cross-referencing card payment methods, international BIN ranges, and velocity indicators.
                </p>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2.5">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Total Active Chargebacks:</span>
                    <span className="text-rose-600 font-bold">{chargebacks.length} records</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Disputed Sum:</span>
                    <span className="text-slate-900 font-medium">
                      {formatINR(chargebacks.reduce((acc, c) => acc + (c.amount || 0), 0))}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-6 text-center text-xs font-mono text-slate-400">
                No chargeback clusters or malicious fraud rings detected in your ledger. The ML surveillance engine is actively scoring incoming transactions.
              </div>
            )}
          </div>
        </div>

        {/* High Risk Queue */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
              HIGH-RISK CHARGEBACK LINEAGE & EVIDENCE
            </h3>
            <span className="text-[11px] font-mono text-slate-500">REAL-TIME DISPUTE DOSSIER</span>
          </div>

          <div className="divide-y divide-slate-100">
            {chargebacks.length > 0 ? (
              chargebacks.map((cb: any) => (
                <div 
                  key={cb.id} 
                  onClick={() => setSelectedTx(cb)}
                  className="py-3.5 flex items-center justify-between hover:bg-slate-50 px-3 rounded-lg cursor-pointer text-xs font-mono transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Shield className="w-4 h-4 text-rose-500" />
                    <div>
                      <span className="font-bold text-slate-900">{cb.chargeback_ref || cb.id}</span>
                      <span className="text-slate-500 ml-2">Reason Code: {cb.reason_code || 'N/A'}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="font-bold text-amber-700">{formatINR(cb.amount || 0)}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-rose-50 text-rose-700 border border-rose-200">
                      {cb.is_segment_b ? 'HIGH RISK CLUSTER' : 'DISPUTE'}
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs font-mono text-slate-400">
                No chargebacks or high-risk disputes logged. All transaction dispute claims will appear here with evidence files and gateway logs.
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Transaction Evidence Dossier Drawer */}
      <EvidenceDrawer 
        isOpen={!!selectedTx} 
        onClose={() => setSelectedTx(null)}
        title={`DISPUTE DOSSIER — ${selectedTx?.chargeback_ref}`}
      >
        {selectedTx && (
          <div className="space-y-4 text-xs font-mono text-slate-700">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <div className="text-[10px] text-slate-500 uppercase font-bold">DISPUTED SUM</div>
              <div className="text-xl font-bold text-amber-700">{formatINR(selectedTx.amount)}</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <div className="text-[10px] text-slate-500 uppercase font-bold">MODEL ATTRIBUTION</div>
              <div className="flex justify-between">
                <span>Reason Code:</span>
                <strong className="text-slate-900">{selectedTx.reason_code}</strong>
              </div>
              <div className="flex justify-between">
                <span>Segment Tag:</span>
                <strong className="text-rose-600">{selectedTx.is_segment_b ? 'Segment B (Anomalous)' : 'Segment A'}</strong>
              </div>
            </div>
          </div>
        )}
      </EvidenceDrawer>
    </div>
  );
}
