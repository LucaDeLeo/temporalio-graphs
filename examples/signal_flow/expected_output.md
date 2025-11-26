# Expected Output: Cross-Workflow Signal Flow

This document shows the expected Mermaid output when analyzing workflows with
cross-workflow signal connections using `analyze_signal_graph()`.

## Signal Chain: Order -> Shipping -> Notification

This example demonstrates a three-workflow signal chain where:

1. **OrderWorkflow** sends `ship_order` signal to ShippingWorkflow
2. **ShippingWorkflow** handles `ship_order` and sends `notify_shipped` signal
3. **NotificationWorkflow** handles `notify_shipped` signal

### Expected Mermaid Diagram

```mermaid
flowchart TB
    subgraph OrderWorkflow
        s_OrderWorkflow((Start))
        process_order_OrderWorkflow[process order]
        ext_sig_ship_order_43_OrderWorkflow[/Signal 'ship_order' to shipping-{*}\]
        complete_order_OrderWorkflow[complete order]
        e_OrderWorkflow((End))
        s_OrderWorkflow --> process_order_OrderWorkflow
        process_order_OrderWorkflow --> ext_sig_ship_order_43_OrderWorkflow
        ext_sig_ship_order_43_OrderWorkflow --> complete_order_OrderWorkflow
        complete_order_OrderWorkflow --> e_OrderWorkflow
        sig_handler_ship_order_67{{ship_order}}
    end

    subgraph ShippingWorkflow
        s_ShippingWorkflow((Start))
        ship_package_ShippingWorkflow[ship package]
        ext_sig_notify_shipped_56_ShippingWorkflow[/Signal 'notify_shipped' to notification-{*}\]
        e_ShippingWorkflow((End))
        s_ShippingWorkflow --> ship_package_ShippingWorkflow
        ship_package_ShippingWorkflow --> ext_sig_notify_shipped_56_ShippingWorkflow
        ext_sig_notify_shipped_56_ShippingWorkflow --> e_ShippingWorkflow
        sig_handler_ship_order_63{{ship_order}}
    end

    subgraph NotificationWorkflow
        s_NotificationWorkflow((Start))
        send_notification_NotificationWorkflow[send notification]
        e_NotificationWorkflow((End))
        s_NotificationWorkflow --> send_notification_NotificationWorkflow
        send_notification_NotificationWorkflow --> e_NotificationWorkflow
        sig_handler_notify_shipped_55{{notify_shipped}}
    end

    %% Cross-workflow signal connections
    ext_sig_ship_order_43_OrderWorkflow -.ship_order.-> sig_handler_ship_order_63
    ext_sig_notify_shipped_56_ShippingWorkflow -.notify_shipped.-> sig_handler_notify_shipped_55

    %% Signal handler styling (hexagons - blue)
    style sig_handler_ship_order_63 fill:#e6f3ff,stroke:#0066cc
    style sig_handler_notify_shipped_55 fill:#e6f3ff,stroke:#0066cc
```

### Visualization Features

- **Subgraphs**: Each workflow is rendered as a separate subgraph block with `subgraph WorkflowName ... end`
- **Signal handlers**: Hexagon nodes `{{signal_name}}` show where signals are received
- **Cross-subgraph edges**: Dashed edges `-.signal_name.->` connect signal sends to handlers
- **Blue styling**: Signal handler hexagons use blue color `fill:#e6f3ff,stroke:#0066cc`
- **External signal trapezoids**: `[/Signal 'name' to target\]` show signal sends

### Key Syntax Elements

| Element | Mermaid Syntax | Purpose |
|---------|---------------|---------|
| Subgraph wrapper | `subgraph Name ... end` | Groups workflow nodes |
| Signal handler | `{{signal_name}}` | Hexagon for signal reception |
| External signal | `[/Signal 'name' to target\]` | Trapezoid for signal send |
| Cross-workflow edge | `-.signal_name.->` | Dashed edge between workflows |
| Handler styling | `fill:#e6f3ff,stroke:#0066cc` | Blue color for hexagons |

### Signal Types Comparison

This example uses **peer-to-peer signals** (Epic 7-8), which are distinct from:

1. **Internal Signals (Epic 4)**: `wait_condition()` for workflow's own state changes
   - Visualization: Hexagon node `{{Wait: condition_name}}`
   - Color: Blue (`#e6f3ff` fill, `#0066cc` stroke)

2. **Parent-Child (Epic 6)**: `execute_child_workflow()` for synchronous spawning
   - Visualization: Subroutine node `[[ChildWorkflowName]]`
   - Color: Green (`#e6ffe6` fill, `#00cc00` stroke)

3. **Peer-to-Peer (Epic 7-8)**: `get_external_workflow_handle().signal()` for async communication
   - Visualization: Trapezoid node `[/Signal 'name' to target\]` + hexagon handler `{{name}}`
   - Colors: Orange/amber for sends, blue for handlers

### Unresolved Signals

When a signal is sent to a workflow that doesn't exist in the search paths,
it appears as an unresolved signal with a dead-end node:

```mermaid
%% Unresolved signals (no handler found)
ext_sig_unknown_42 -.unknown_signal.-> unknown_unknown_signal_42[/?/]

%% Unresolved signal styling (warning - amber)
style unknown_unknown_signal_42 fill:#fff3cd,stroke:#ffc107
```

The `[/?/]` node with amber styling indicates a signal that couldn't be resolved
to any handler in the search paths.
