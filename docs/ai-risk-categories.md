# The eight AI risk categories — prompts and example scenarios

The register uses eight categories. For each system in pilot or production, go through the prompts below and write at
least one risk per category that applies — or note why it does not. Scenarios are fictional and sized for a mid-sized
organisation; adapt the numbers.

## 1. Bias & fairness

**Prompts:** Which groups could be treated differently by this system? Are there proxies for protected
characteristics in the features or prompts? Has anyone measured error rates or selection rates per group on *our*
population, not the vendor's? Can an affected person contest an outcome?

**Scenarios:** hiring model down-ranks applicants with career gaps · fraud model flags customers from certain postcodes
more often · support assistant gives shorter answers to non-native phrasing.

**Typical controls:** disparate-impact testing per group and per release, feature review, human review of adverse
outcomes, appeal path. ISO 42001: A.5.4, A.6.2.4, A.7.4.

## 2. Transparency & explainability

**Prompts:** Do people know AI is involved? Can we explain an individual outcome in terms a regulator or a customer
accepts? Is the output presented with the confidence and sources it deserves? Can staff tell when to distrust it?

**Scenarios:** chatbot presents guesses as facts · credit decision cannot be explained to the applicant · managers
treat a ranking as objective truth.

**Typical controls:** disclosure, citations and confidence, model cards, decision records, training for users.
ISO 42001: A.8.2, A.9.3, A.9.4.

## 3. Robustness & drift

**Prompts:** What happens when the world changes (new region, new product, new season)? Which inputs are out of
distribution? How would we know the model got worse — before customers tell us? Is there a rollback?

**Scenarios:** ETA model wrong after network change · document classifier fails on a new form layout · generative model
hallucinates after a provider update.

**Typical controls:** input and output drift monitoring, business-metric alerts tied to model version, retrain
triggers, canary releases, rollback. ISO 42001: A.6.2.6, A.6.2.8, A.7.6.

## 4. Privacy

**Prompts:** What personal data enters training, retrieval, prompts and logs? Is the purpose the one we told people?
Does the provider retain or train on our data? Could the model memorise and reveal personal data? Is a DPIA needed?

**Scenarios:** complaints with names sent to a third-party API · support history reused to drive marketing · model
reproduces a customer's address from training data.

**Typical controls:** minimisation and pseudonymisation before prompting, contractual no-retention and no-training
clauses, purpose tags, retention limits, DPIA. ISO 42001: A.7.3, A.7.5, A.10.3.

## 5. Security

**Prompts:** Can untrusted content reach the model (user text, documents, web pages, tool results)? What can the model
trigger, with whose permissions? Who can change training or retrieval data? Could someone extract the model or the
prompt? Is the model supply chain (weights, datasets, libraries) verified?

**Scenarios:** prompt injection makes an assistant reveal other customers' data · poisoned tickets steer
recommendations · unsigned model download from a public hub carries malicious code · API key abuse burns the budget.

**Typical controls:** retrieval authorisation before prompting, user content as data not instructions, least-privilege
tools with approval for consequential actions, signed datasets and model artefacts, quotas and spend alerts, adversarial
testing. ISO 42001: A.6.2.4, A.6.2.6, A.7.4; ISO 27001: A.8.3, A.8.26, A.8.28, A.8.29. For a per-element threat list,
run the sibling [threat-modeling-toolkit](https://github.com/bizidwassim-design/threat-modeling-toolkit) with `ai: true`.

## 6. Safety

**Prompts:** Can acting on the output hurt someone physically, psychologically or financially? Does the optimisation
objective conflict with a safety rule? Is there a human who can actually stop it in time? What is the fallback when the
model is unavailable or obviously wrong?

**Scenarios:** route optimiser compresses driver breaks · maintenance predictor suppresses a real alarm · assistant
gives dangerous handling instructions for chemicals.

**Typical controls:** safety rules as hard constraints, output filters for dangerous domains, meaningful human approval,
kill switch and tested fallback. ISO 42001: A.5.4, A.6.1.2, A.6.2.2.

## 7. Accountability & oversight

**Prompts:** Who owns the system (one role)? Who approves a new model version, on what evidence? Can we reconstruct
which version produced a given output? Is there an incident process that includes "the model did something wrong"? Does
the oversight person have the time, information and authority to intervene?

**Scenarios:** data team promotes models without sign-off · no one can say which model version produced a disputed
decision · "human in the loop" approves 400 items an hour.

**Typical controls:** named owner, release checklist and approval gate, model registry, version in event logs,
AI incidents in the incident process, oversight workload limits. ISO 42001: A.3.2, A.4.2, A.6.2.3, A.6.2.5, A.6.2.8.

## 8. Legal & regulatory (EU AI Act and others)

**Prompts:** What is the EU AI Act category, and who confirmed it? Which obligations follow from being provider or
deployer? Do sector rules apply (financial services, health, employment law, consumer protection)? Who owns the IP in
inputs and outputs? What does the contract with the model provider say about liability, retention and changes?

**Scenarios:** employment screening used without the deployer duties · generated marketing content infringes a
trademark · provider changes the model and the terms with 30 days' notice.

**Typical controls:** documented classification, obligations checklist per system, contract clauses, registration where
required, legal review on significant change. ISO 42001: A.2.2, A.3.2, A.8.2, A.10.3.

## One system, eight rows?

Not always. A minimal-risk, internal, non-personal-data forecasting model may legitimately have two or three rows and
"not applicable — no personal data" noted for the rest. A customer-facing generative assistant in a regulated sector will
usually fill all eight. The goal is a conscious answer per category, not a quota.
