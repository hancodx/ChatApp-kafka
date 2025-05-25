# Real-Time Chat with Apache Kafka

**A demonstration of Apache Kafka as a messaging backbone for real-time communication**

## Core Kafka Implementation

This project showcases Apache Kafka as the distributed messaging platform for a chat application, featuring:

- **Dynamic Kafka Topics**:
  - Dedicated topic per private conversation (`baseTopic-user1-user2`)
  - Group chat topics (`baseTopic-group-groupName`)

- **Implemented Patterns**:
  - Producer/Consumer message exchange
  - Distributed message storage via Kafka
  - Real-time client synchronization

## Kafka Architecture

[Client A] → (Producer) → [Kafka Broker]
↓
[Kafka Broker] → (Consumer) → [Client B]

![deepseek_mermaid_20250523_deb4e1](https://github.com/user-attachments/assets/d43d1c55-fcb3-40e8-9e74-8eb83e162cc3)

![deepseek_mermaid_20250523_1c7c83](https://github.com/user-attachments/assets/37e56626-2a1b-496c-a40e-aeea43e9cba2)

