package global

import (
	svccore "github.com/venndev/vrecommendation/internal/services/core"
	lgcore "github.com/venndev/vrecommendation/pkg/logger/core"
	kfcore "github.com/venndev/vrecommendation/pkg/messaging/core"
	"github.com/venndev/vrecommendation/pkg/setting"
)

var (
	Config       setting.Config
	Logger       lgcore.Logger
	KafkaManager kfcore.KafkaManager
	EventService svccore.EventService
)
