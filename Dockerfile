# Copyright 2026 EOEPCA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Stage 1: Build stage
FROM rockylinux:9.3-minimal AS build

# Install necessary build tools
RUN microdnf install -y curl tar && microdnf clean all

# Download the hatch tar.gz file from GitHub
RUN curl -L https://github.com/pypa/hatch/releases/latest/download/hatch-x86_64-unknown-linux-gnu.tar.gz -o /tmp/hatch-x86_64-unknown-linux-gnu.tar.gz

# Extract the hatch binary
RUN tar -xzf /tmp/hatch-x86_64-unknown-linux-gnu.tar.gz -C /tmp/

# Stage 2: Final stage
FROM rockylinux:9.3-minimal

# Install runtime dependencies
RUN microdnf install -y --nodocs which expat git && \
    microdnf clean all

# Set up a default user and home directory
ENV HOME=/home/appuser

RUN useradd -u 1001 -r -g 100 -m -d ${HOME} -s /sbin/nologin \
  -c "Default appuser User" appuser && \
    mkdir -p /app && \
    mkdir -p /prod && \
    mkdir -p /home/appuser/.cache/pyapp/locks && \
    chown -R 1001:100 /home/appuser/.cache && \
    chown -R 1001:100 /app && \
    chmod g+rwx ${HOME} /app

# Copy the hatch binary from the build stage
COPY --from=build /tmp/hatch /usr/bin/hatch

# Ensure the hatch binary is executable
RUN chmod +x /usr/bin/hatch

# Switch to the non-root user
USER appuser

# Copy the application files into the /app directory
COPY --chown=1001:100 src/ /app

WORKDIR /app

# Set up virtual environment paths
ENV VIRTUAL_ENV=/app/envs/appuser
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV HATCH_PYTHON_VARIANT_LINUX=v2

# Prune any existing environments and create a new production environment
RUN hatch env prune && \
    hatch env create prod && \
    pip install /pymate/. && \
    rm -fr /app/.git /app/.pytest_cache

# Set the command to run the FastAPI app
CMD ["uvicorn", "wes-gateway.main:app", "--host", "0.0.0.0", "--port", "8090"]
