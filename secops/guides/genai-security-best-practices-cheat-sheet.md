GenAI Security Best Practices Cheat Sheet

Migration docs:
- Deployment notes: `C:\telo\Atlas\Memory\DEPLOY.md`
- Rollback map: `C:\telo\Atlas\Memory\MIGRATION-ROLLBACK.md`

AI and GenAI have become essential pillars for organizations aiming to enhance productivity and innovation. As the speed of AI releases and AI adoption accelerates, securing these AI pipelines takes on even greater importance. AI risks are multi-faceted, and they require both existing SecOps techniques and new SecOps practices to evolve to address the unique challenges and characteristics of AI models and deployments.

The task for security teams is no small feat: Not only do you need to grasp the numerous technical aspects of AI but also understand the broader AI security landscape. You then need to gain visibility into AI usage within your organization before you can establish security-first processes to detect and respond to AI risks and threats effectively.

The key principles and objectives in this process include:  
\* Visibility  
\* Zero critical risks  
\* Democratization  
\* Prevention

\#\# Recap: What security risks come with GenAI?

GenAI is about generating new content from unstructured inputs (e.g., text, images, audio) that are extremely varied in format and inherently noisy. To allow for this creativity, GenAI carries new risks in terms of content anomalies, data protection, and AI application security. Across these three categories, primary risks companies must keep an eye on include:  
\* \*\*Data poisoning:\*\* Maliciously altering training data to corrupt an AI model's outputs.  
\* \*\*Model theft:\*\* Unauthorized access and duplication of proprietary AI models.  
\* \*\*Adversarial attacks:\*\* Crafting inputs to steer AI models towards outputting incorrect, misleading, or harmful content.  
\* \*\*Model inversion attacks:\*\* Sending queries to an AI model to obtain sensitive training data.  
\* \*\*Supply chain vulnerabilities:\*\* Exploiting weaknesses in the AI supply chain, such as third-party software dependencies, to compromise AI systems.

\---

\#\# Top 7 GenAI Security Practices

\#\#\# 1\. Remove shadow AI  
To ensure robust AI security, the first step is to achieve full visibility into what you are defending. This means eliminating any unauthorized AI usage within your organization.  
\* \*\*Prerequisite:\*\* Everybody in your organization should know what they can and cannot do with GenAI. Make sure to add simple-to-follow GenAI security practices in the organization's general security guide.  
\* Create an AI-BOM, i.e., a bill of materials collecting all your AI-related assets, ideally capable of automatically detecting new AI use.  
\* Set up relevant networking to ensure access for only whitelisted GenAI providers and software, or to block access to all those blacklisted.  
\* Foster education and awareness aimed at promoting a security-first mindset.

By blocking Shadow AI, you minimize the chances of unexpected and unseen vulnerabilities for which you have no security controls in place; you also avoid any associated compliance issues.

\#\#\# 2\. Protect your data  
Safeguarding sensitive information is crucial to maintaining organizational security and regulatory compliance. No sensitive information should be used in GenAI web and SaaS applications unless secured and approved, and no training data should be exposed and accessible through the GenAI model and application.  
\* \*\*Prerequisite:\*\* Your team should agree with business and technical stakeholders on a definition of what constitutes sensitive information in your organization, possibly with different levels of criticality.  
\* Discover and classify your data according to its security criticality.  
\* Use encryption for data at rest and in transit.  
\* Perform data sanitization such as removing or masking PII information for training data sets.  
\* Configure data loss prevention (DLP) policies to avoid sensitive data being used in end-user applications.  
\* Audit who has access to which data to understand effective access.

\#\#\# 3\. Secure access to GenAI models  
Unauthorized agents gaining access to GenAI models could deploy a variety of techniques to modify and misuse the model, such as introducing biases or harmful deceptions.  
\* \*\*Prerequisite:\*\* A well-defined IAM configuration is a must-have for all assets associated with GenAI deployments and applications, with role-based access control (RBAC) recommended.  
\* Set up authentication and rate limiting for API usage.  
\* Restrict access to model weights.  
\* Allow only required users to kickstart model training and deployment pipelines.

\#\#\# 4\. Use LLM built-in guardrails  
Following a multi-layer security-first mindset, it is always ideal to introduce security at the source by incorporating built-in guardrails of your GenAI models as security controls.  
\* \*\*Prerequisite:\*\* Thoroughly review the documentation of GenAI providers and models to ensure they provide support for your designated guardrails.  
\* Content filtering to automatically remove or flag inappropriate or harmful content.  
\* Abuse detection mechanisms to uncover and mitigate general model misuse.  
\* Temperature settings to change AI output randomness to your desired predictability.

\#\#\# 5\. Detect and remove AI risks and attack paths  
Attack path analysis (APA) preemptively identifies end-to-end attack paths composed of complex chains of exposures and lateral movement paths in your AI systems.  
\* \*\*Prerequisite:\*\* End-to-end risk monitoring of your AI infrastructure with clear lineage and full context.  
\* Continuously scan for and identify vulnerabilities in AI models.  
\* Verify all systems and components have the most recent patches to close known vulnerabilities.  
\* Scan for malicious models.  
\* Assess for AI misconfigurations, effective permissions, network exposures, exposed secrets, and sensitive data to detect attack paths.  
\* Regularly audit access controls to guarantee only authorized parties are granted access to critical systems.  
\* Provide context around AI risks so that you can proactively remove attack paths to models via remediation guidance.

\#\#\# 6\. Monitor against anomalies  
Continuous monitoring can help detect and address unusual activities in your AI systems promptly.  
\* \*\*Prerequisite:\*\* A thorough monitoring solution should be put in place that provides extended detection for suspicious activity in GenAI applications.  
\* Use anomaly detection and behavior analytics at both the input and output.  
\* Detect suspicious behavior in AI pipelines.  
\* Keep track of unexpected spikes in latency and other system metrics.  
\* Support regular security audits and assessments.

\#\#\# 7\. Set up incident response  
Preparing a swift incident response plan is critical to minimizing the blast radius of AI-related security incidents.  
\* \*\*Prerequisite:\*\* A general incident response team should be available for critical AI systems and be able to rely on security tools designed for easy understanding of AI threats.  
\* Processes for isolation, backup, traffic control, and rollback.  
\* Integration with SecOps tools.  
\* Availability of an AI-focused incident response plan.

\---

\#\# What's next?  
A proactive and agile approach to AI and GenAI security is necessary to keep up with the speed of development and adoption of these technologies. An AI-SPM tool that supports security teams in setting up their AI posture with built-in best practices and automated processes is a big differentiator for ensuring that GenAI brings only the desired benefits to your organization.