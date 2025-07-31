package global

import (
	"github.com/venndev/vrecommendation/pkg/logger"
	"github.com/venndev/vrecommendation/pkg/messaging"
	"github.com/venndev/vrecommendation/pkg/setting"
)

var (
	Config        setting.Config
	Logger        *logger.Logger
	MessageBroker messaging.MessageBroker
)
