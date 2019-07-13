import { storiesOf } from "@storybook/react";
import React from "react";

import Timeline, {
  TimelineEvent,
  TimelineNote
} from "@saleor/components/Timeline";
import Decorator from "../../Decorator";

storiesOf("Generics / Timeline", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <Timeline>
      <TimelineEvent
        date="2018-05-07T16:58:02+00:00"
        title="Expansion panel 1"
      />
      <TimelineEvent
        date="2018-05-07T16:48:02+00:00"
        title="Expansion panel 2"
      />
      <TimelineEvent
        date="2018-05-06T16:58:02+00:00"
        title="Expansion panel 3"
      />
    </Timeline>
  ))
  .add("with expansion panels", () => (
    <Timeline>
      <TimelineEvent date="2018-05-07T16:58:02+00:00" title="Expansion panel 1">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineEvent>
      <TimelineEvent date="2018-05-07T16:48:02+00:00" title="Expansion panel 2">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineEvent>
      <TimelineEvent date="2018-05-06T16:58:02+00:00" title="Expansion panel 3">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineEvent>
    </Timeline>
  ))
  .add("with order notes", () => (
    <Timeline>
      <TimelineEvent date="2018-05-07T16:58:02+00:00" title="Expansion panel 1">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineEvent>
      <TimelineNote
        date="2018-05-07T16:58:02+00:00"
        user={{ email: "admin@example.com" }}
        message="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget."
      />
      <TimelineNote
        date="2018-05-07T16:58:02+00:00"
        user={{ email: "ceo@example.com" }}
        message="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget."
      />
      <TimelineEvent date="2018-05-06T16:58:02+00:00" title="Expansion panel 3">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineEvent>
    </Timeline>
  ));
