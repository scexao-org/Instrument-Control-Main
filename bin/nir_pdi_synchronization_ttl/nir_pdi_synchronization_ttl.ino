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

double max_integration_time = 1000000;
double min_integration_time = 100;

double beginning_time;
double end_time1;
double end_time2;
double end_time3;
double end_time4;
double end_time5;
double end_time6;

double integration_time;
double pulse_width;
double flc_offset;
int trigger_mode;

void setup() {
	Serial.begin(115200);
  Serial.setTimeout(1);

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

void loop() {
	if (Serial.available()) {
		integration_time = Serial.parseInt();
    pulse_width = Serial.parseInt();
		flc_offset = Serial.parseInt();
		trigger_mode = Serial.parseInt();
		
    if (integration_time > max_integration_time) {
      Serial.println("ERROR - frequency too low.");
    }
    else if (integration_time < min_integration_time) {
      Serial.println("ERROR - frequency too high.");
    }
    else if (flc_offset < 0 || flc_offset + pulse_width >= integration_time ) {
      Serial.println("ERROR - flc_offset invalid: > 0 and < width+period");
    }
		else {
			Serial.print("Starting series with parameters ");
			Serial.print(integration_time);
			Serial.print(" ");
      Serial.print(pulse_width);
      Serial.print(" ");
			Serial.print(flc_offset);
			Serial.print(" ");
			Serial.print(trigger_mode);
			Serial.print(" ");

			if (trigger_mode == 1) {
        digitalWrite(flc_control_pin, HIGH);
			}

      Serial.println("start trigger signal.");
      beginning_time = micros();

		  for (;;) {
        // One loop pass covers 2 exposure times with 2 polarizations
			  // First pola flc_pin HIGH
			  end_time1 = beginning_time + flc_offset;
        end_time2 = end_time1 + pulse_width;
        end_time3 = beginning_time + integration_time;

        // Second pola flc_pin LOW
        end_time4 = end_time1 + integration_time;
        end_time5 = end_time2 + integration_time;
        end_time6 = end_time3 + integration_time;
        
        beginning_time = end_time6;
        
			  for (;micros() < end_time1;) {
			  }
        digitalWrite(camera_pin_p, HIGH);
			  for (;micros() < end_time2;) {
			  }
        digitalWrite(camera_pin_p, LOW);
        for (;micros() < end_time3;) {
        }
        digitalWrite(flc_pin, HIGH);
        for (;micros() < end_time4;) {
        }
			  digitalWrite(camera_pin_p, HIGH);
			  for (;micros() < end_time5;) {
			  }
			  digitalWrite(camera_pin_p, LOW);
			  for (;micros() < end_time6;) {
			  }
        digitalWrite(flc_pin, LOW);
		  }
		}

		digitalWrite(flc_pin, LOW);
		digitalWrite(flc_control_pin, LOW);

		Serial.println("OK - data obtaining complete.");
	}
}
