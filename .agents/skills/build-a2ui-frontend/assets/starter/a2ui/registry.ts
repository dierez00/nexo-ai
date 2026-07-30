import {
  AudioPlayer,
  Button,
  Card,
  CheckBox,
  ChoicePicker,
  Column,
  DateTimeInput,
  Divider,
  Icon,
  Image,
  List,
  Modal,
  Row,
  Slider,
  Tabs,
  Text,
  TextField,
  Video,
  type ReactComponentImplementation,
} from "@a2ui/react/v0_9";
import {
  Catalog,
  MessageProcessor,
  type ActionListener,
} from "@a2ui/web_core/v0_9";
import { BASIC_FUNCTIONS } from "@a2ui/web_core/v0_9/basic_catalog";

import {
  Checklist,
  ConfirmationSummary,
  DataTable,
  MetricCard,
  RunTimeline,
  SourceCitation,
  StatusBanner,
  WorkflowGraph,
} from "./nexo-components";
import { assertSafeA2UIMessages } from "./message-guard";

export const CITIZEN_CATALOG_ID =
  "urn:nexo-ia:a2ui:catalog:citizen:v1" as const;
export const ADMIN_CATALOG_ID =
  "urn:nexo-ia:a2ui:catalog:admin:v1" as const;

const basicComponents: ReactComponentImplementation[] = [
  Text,
  Image,
  Icon,
  Video,
  AudioPlayer,
  Row,
  Column,
  List,
  Card,
  Tabs,
  Divider,
  Modal,
  Button,
  CheckBox,
  TextField,
  DateTimeInput,
  ChoicePicker,
  Slider,
];

const sharedComponents: ReactComponentImplementation[] = [
  StatusBanner,
  SourceCitation,
  Checklist,
];

export const citizenCatalog = new Catalog<ReactComponentImplementation>(
  CITIZEN_CATALOG_ID,
  [...basicComponents, ...sharedComponents, ConfirmationSummary],
  BASIC_FUNCTIONS,
);

export const adminCatalog = new Catalog<ReactComponentImplementation>(
  ADMIN_CATALOG_ID,
  [
    ...basicComponents,
    ...sharedComponents,
    MetricCard,
    DataTable,
    RunTimeline,
    WorkflowGraph,
  ],
  BASIC_FUNCTIONS,
);

export const nexoCatalogs = [citizenCatalog, adminCatalog] as const;

export function createNexoMessageProcessor(actionHandler?: ActionListener) {
  return new MessageProcessor<ReactComponentImplementation>(
    [...nexoCatalogs],
    actionHandler,
    { version: "v0.9.1" },
  );
}

export function processNexoMessages(
  processor: ReturnType<typeof createNexoMessageProcessor>,
  messages: unknown,
  onValidationError?: (error: unknown) => void,
):
  | { ok: true }
  | {
      ok: false;
      error: {
        code: "VALIDATION_FAILED";
        message: "La surface A2UI no superó la validación.";
      };
      requiresProcessorReset: true;
    } {
  try {
    assertSafeA2UIMessages(messages);
    processor.processMessages(
      messages as Parameters<typeof processor.processMessages>[0],
    );
    return { ok: true };
  } catch (error) {
    onValidationError?.(error);
    return {
      ok: false,
      error: {
        code: "VALIDATION_FAILED",
        message: "La surface A2UI no superó la validación.",
      },
      requiresProcessorReset: true,
    };
  }
}
