# Exit Ticket

## 1. Case nào nên dùng multi-agent? Vì sao?

Multi-agent phù hợp với research task có nhiều sub-question độc lập, cần nhiều loại evidence, hoặc cần tách generation khỏi verification. Khi Researcher và Analyst có trách nhiệm khác nhau, handoff có artifact/provenance rõ ràng, việc tách agent có thể tăng coverage và phát hiện unsupported claims.

## 2. Case nào không nên dùng multi-agent? Vì sao?

Không nên dùng multi-agent cho câu hỏi hẹp, ít nguồn, hoặc khi một model mạnh có thể hoàn thành trong một context duy nhất. Khi decomposition không tạo thêm thông tin hay verification độc lập, coordination overhead làm tăng latency/token cost và tạo thêm điểm failure ở handoff.
