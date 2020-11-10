# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the License);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an AS IS BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading

DEVICE_ID = "deviceId"
TRANSLATION = "translation"
STATES = "states"
UNITS = "unit_values"

class TelemetryValidator(object):
  """TODO"""

  def __init__(self, entities, timeout, callback):
    super().__init__()
    self.entities = entities
    self.timeout = timeout
    self.callback = callback
    self.validated_entities = {}
    self.validation_errors = {}

  def StartTimer(self, timeout):
    threading.Timer(timeout, lambda: self.callback(self)).start()

  def AllEntitiesValidated(self):
    return self.entities.len() == self.validated_entities.len()

  def CheckAllEntitiesValidated(self):
    if self.AllEntitiesValidated():
      self.callback(self)

  def AddError(self, error):
    self.validation_errors.append(error)

  def ValidateMessage(self, message):
    t = telemetry.Telemetry(message)
    entity = t.attributes[DEVICE_ID]

    if entity not in self.entities:
      self.AddError(TelemetryError(entity, None, "Unknown entity"))
      message.ack()
      return

    if entity in self.validated_entities:
      # Already validated telemetry for this entity, so the message can be skipped.
      return
    self.validated_entities[entity] = True

    entity = entities[t.entity_name]
    for point_name, point_config in entity[TRANSLATION]:
      if point_name not in t.points.keys():
        self.AddError(TelemetryError(entity, point_name, "Missing point"))
        continue

      point = t.points[point_name]
      pv = point.present_value
      if pv == None:
        self.AddError(TelemetryError(entity, point_name, "Missing present value"))
        continue

      has_states = STATES in point_config
      has_units = UNITS in point_config

      if has_states:
        states = point_config[STATES]
        if pv not in states.values():
          self.AddError(TelemetryError(entity, point_name, "Invalid state: " + pv))
          continue

      if value_is_numeric(pv):
        if value_is_integer(pv):
          if not (has_states or has_units):
            self.AddError(TelemetryError(entity, point_name, "Integer value without states or units: " + pv))
        elif not has_units:
            self.AddError(TelemetryError(entity, point_name, "Numeric value without units: " + pv))

    message.ack()
    self.CheckAllEntitiesValidated()

  def value_is_numeric(value):
    try:
      float(value)
    except ValueError:
      return False
    return True

  def value_is_integer(value):
    try:
      return int(value) == float(value)
    except ValueError:
      return False
