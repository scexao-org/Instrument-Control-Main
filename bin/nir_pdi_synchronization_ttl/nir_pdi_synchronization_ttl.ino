//#define camera_pin_p DAC0
//#define camera_pin_n DAC1
#define camera_pin_p 39
#define flc_pin 10
#define flc_control_pin 8
#define lvds_vcc 6
#define trigger_pin 2

//#define LVDS_HIGH 1.375
//#define LVDS_LOW 1.025
//#define VOLTAGE_OUTPUT 3.3

// FYI C people: Arduino int is 16bit, long is 32 bits.
// We use unsigned long for everything time-related in microseconds.
unsigned long max_integration_time = 1000000;
unsigned long min_integration_time = 100;
unsigned long beginning_time;
unsigned long last_reset;
unsigned long dt1;
unsigned long dt2;
unsigned long dt3;
unsigned long dt4;
unsigned long dt5;
unsigned long dt6;
unsigned long integration_time;
unsigned long pulse_width;
unsigned long flc_offset;

int trigger_mode;

int sweep_mode = 0;
int auto_reset_mode = 0;
unsigned long next_reset = 0;

void setup()
{
  Serial.begin(115200);
  Serial.setTimeout(500);

  pinMode(camera_pin_p, OUTPUT);
  digitalWrite(camera_pin_p, 0);
  pinMode(flc_pin, OUTPUT);
  digitalWrite(flc_pin, LOW);
  pinMode(flc_control_pin, OUTPUT);
  digitalWrite(flc_control_pin, LOW);
  pinMode(trigger_pin, INPUT);
  pinMode(lvds_vcc, OUTPUT);
  digitalWrite(lvds_vcc, HIGH);
}

void loop()
{
  if (Serial.available())
  {
    integration_time = Serial.parseInt();

    if (integration_time == 0) {
      Serial.println("Arduino abort");
      return;
    }

    pulse_width = Serial.parseInt();
    flc_offset = Serial.parseInt();
    trigger_mode = Serial.parseInt();

    if (integration_time > max_integration_time)
    {
      Serial.println("ERROR - frequency too low.");
    }
    else if (integration_time < min_integration_time)
    {
      Serial.println("ERROR - frequency too high.");
    }
    else if (flc_offset < 0 || flc_offset + pulse_width >= integration_time)
    {
      Serial.println("ERROR - flc_offset invalid: > 0 and < width+period");
    }
    else // All serial parameters valid
    {
      Serial.print("Starting series with parameters ");
      Serial.print(integration_time);
      Serial.print(" ");
      Serial.print(pulse_width);
      Serial.print(" ");
      Serial.print(flc_offset);
      Serial.print(" ");
      Serial.print(trigger_mode);
      Serial.print(" \n");

      if (trigger_mode & 0x1)
      { // Use LSB to define FLC polarity
        digitalWrite(flc_control_pin, HIGH);
      }
      if (trigger_mode & 0x2)
      { // Use 2nd bit for sweep
        sweep_mode = 1;
      }
      if (trigger_mode & 0x4)
      { // Use 3rd bit for auto-reset (for EDT FG).
        auto_reset_mode = 1;
      }

      Serial.print("start trigger signal.\n");

      // Compute values for loop

      last_reset = micros();

      dt1 = flc_offset;
      dt2 = dt1 + pulse_width;
      dt3 = integration_time;

      // Asymmetric triggering by triggering the second frame 20 us too late (see below)
      dt4 = dt1 + integration_time + 20; // 20 us for measurable FLC on / FLC off skew
      dt5 = dt2 + integration_time + 20;
      dt6 = dt3 + integration_time;

      for (;;)
      {
        beginning_time = micros();
        // One loop pass covers 2 exposure times with 2 polarizations

        // First pola flc_pin LOW
        for (; micros() - beginning_time < dt1;) // This way of testing works around micros() overflowing
        {
        }
        digitalWrite(camera_pin_p, HIGH);
        for (; micros() - beginning_time < dt2;)
        {
        }
        digitalWrite(camera_pin_p, LOW);
        for (; micros() - beginning_time < dt3;)
        {
        }
        // Second pola flc_pin HIGH
        digitalWrite(flc_pin, HIGH);
        for (; micros() - beginning_time < dt4;)
        {
        }
        digitalWrite(camera_pin_p, HIGH);
        for (; micros() - beginning_time < dt5;)
        {
        }
        digitalWrite(camera_pin_p, LOW);
        for (; micros() - beginning_time < dt6;)
        {
        }
        digitalWrite(flc_pin, LOW);

        // Sweep mode
        if (sweep_mode)
        {
          ++flc_offset;
          if (flc_offset + pulse_width == integration_time)
          {
            flc_offset = 0;
          }
        }

        if (auto_reset_mode && (micros() - last_reset) >= 5000000) // 5 sec
        {
          // Sleep for 150 ms
          // EDT framegrabber set to timeout at 100 ms. Force it to timeout.
          for (; micros() - beginning_time < dt6 + 150000;)
          {
          }
          // Next reset in 5 sec.
          last_reset = micros();
        } // if auto_reset
      }   // For FLC / cam trig loop
    }     // else: All serial parameters valid

    digitalWrite(flc_pin, LOW);
    digitalWrite(flc_control_pin, LOW);

    Serial.println("OK - data obtaining complete.");
  } // if serial available
} // function void loop() {}
