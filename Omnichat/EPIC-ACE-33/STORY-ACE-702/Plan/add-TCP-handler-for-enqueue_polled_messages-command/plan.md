# Plan: Commit 7 — TCP handler for enqueue_polled_messages in omnichat-gateway

## Context
Part of EPIC-ACE-33 ACE-702. Polled messages from marketplace connectors (ACE-703/704/705) need to reach SQS FIFO for normalization. Rather than having omnichat-service call SQS directly, it sends via TCP to omnichat-gateway which already owns the SQS queue layer. This commit wires omnichat-gateway to accept TCP connections and handle the `enqueue_polled_messages` command.

## Commit Message
`feat(omnichat-gateway): add TCP handler for enqueue_polled_messages command`

## Files to Create/Modify

### 1. Modify `ace/packages/config/src/configuration.ts`
Add tcp block to `omnichatGateway` (currently HTTP-only):
```typescript
omnichatGateway: {
  http: { ... },   // existing
  tcp: {
    host: process.env.OMNICHAT_GATEWAY_TCP_HOST || 'localhost',
    port: Number.parseInt(process.env.OMNICHAT_GATEWAY_TCP_PORT as string, 10) || 4001,
  },
},
```

### 2. Modify `ace/apps/omnichat-gateway/src/main.ts`
Add TCP microservice after `NestFactory.create()`, following the same pattern as omnichat-service:
```typescript
const TCP_HOST = configService.get<string>('shared.omnichatGateway.tcp.host');
const TCP_PORT = configService.get<string>('shared.omnichatGateway.tcp.port');

app.connectMicroservice<MicroserviceOptions>({
  transport: Transport.TCP,
  options: { host: TCP_HOST, port: Number.parseInt(TCP_PORT, 10) },
});

await app.startAllMicroservices();
await app.listen(...);
```

### 3. Create `ace/apps/omnichat-gateway/src/polling/polling.controller.ts`
```typescript
@UseInterceptors(LoggingInterceptor)
@Controller()
export class PollingController {
  constructor(private readonly queueService: QueueService) {}

  @MessagePattern('enqueue_polled_messages')
  async enqueuePolledMessages(
    @Payload() messages: RawWebhookMessage[],
  ): Promise<{ status: string; enqueuedCount: number }> {
    for (const message of messages) {
      await this.queueService.sendMessage(message);
    }
    return { status: 'ok', enqueuedCount: messages.length };
  }
}
```
* Errors bubble as `RpcException` (follows `channel-accounts-tcp.controller` pattern)
* `QueueService.sendMessage()` already handles FIFO `MessageGroupId = {platform}-{channelId}-{sourceUserId}` and Redis fallback

### 4. Create `ace/apps/omnichat-gateway/src/polling/polling.module.ts`
```typescript
@Module({
  imports: [QueueModule],
  controllers: [PollingController],
})
export class PollingModule {}
```

### 5. Modify `ace/apps/omnichat-gateway/src/app.module.ts`
Add import statement + `PollingModule` to imports array.

## Patterns to Follow
* TCP bootstrap: `ace/apps/omnichat-service/src/main.ts` (exact same pattern)
* TCP controller: `ace/apps/omnichat-service/src/channel-accounts/channel-accounts-tcp.controller.ts`
* Config TCP block: `packages/config/src/configuration.ts` — `omnichatService.tcp` section
* Default TCP port: 4001 (follows pattern: HTTP 3001 → TCP 4001)

## Verification
* `pnpm --filter omnichat-gateway build` — TypeScript compiles without errors
* `pnpm --filter omnichat-gateway start:dev` — logs show TCP is running on :4001