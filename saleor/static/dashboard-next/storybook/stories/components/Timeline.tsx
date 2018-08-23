import { storiesOf } from "@storybook/react";
import * as React from "react";

import Timeline, {
  TimelineNode,
  TimelineNote
} from "../../../components/Timeline";
import Decorator from "../../Decorator";

storiesOf("Generics / Timeline", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <Timeline>
      <TimelineNode
        date="2018-05-07T16:58:02+00:00"
        title="Expansion panel 1"
      />
      <TimelineNode
        date="2018-05-07T16:48:02+00:00"
        title="Expansion panel 2"
      />
      <TimelineNode
        date="2018-05-06T16:58:02+00:00"
        title="Expansion panel 3"
      />
    </Timeline>
  ))
  .add("with expansion panels", () => (
    <Timeline>
      <TimelineNode date="2018-05-07T16:58:02+00:00" title="Expansion panel 1">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineNode>
      <TimelineNode date="2018-05-07T16:48:02+00:00" title="Expansion panel 2">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineNode>
      <TimelineNode date="2018-05-06T16:58:02+00:00" title="Expansion panel 3">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineNode>
    </Timeline>
  ))
  .add("with order notes", () => (
    <Timeline>
      <TimelineNode date="2018-05-07T16:58:02+00:00" title="Expansion panel 1">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineNode>
      <TimelineNote
        date="2018-05-07T16:58:02+00:00"
        user="admin@example.com"
        content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget."
      />
      <TimelineNote
        date="2018-05-07T16:58:02+00:00"
        user="ceo@example.com"
        content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget."
      />
      <TimelineNode date="2018-05-06T16:58:02+00:00" title="Expansion panel 3">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineNode>
    </Timeline>
  ));
